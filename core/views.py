import os
import io
import re
import uuid
import logging
import threading
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from guide_generator.generator import generate_interview_guide, DEFAULT_INTERVIEW_TIPS, GENERAL_TIPS, FOLLOW_UP_TIPS, _generate_recent_news
from guide_generator.pdf_builder import build_guide_pdf

logger = logging.getLogger(__name__)


def _clean_pasted_text(text: str) -> str:
    """Strip common formatting artifacts from pasted text.

    Handles markdown bold/italic markers, heading hashes, smart quotes,
    non-breaking spaces, excessive whitespace, and other copy-paste noise
    so the PDF renders clean text.
    """
    if not text:
        return text
    # Strip markdown heading markers (## Heading → Heading)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Strip bold/italic markers: **text** → text, __text__ → text, *text* → text
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.+?)_{1,3}', r'\1', text)
    # Strip markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Replace smart/curly quotes with straight ones
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    # Replace non-breaking spaces with regular spaces
    text = text.replace('\u00a0', ' ')
    # Strip leading bullet characters (•, ‣, ◦) that aren't followed by structure
    text = re.sub(r'^[\u2022\u2023\u25e6]\s*', '', text, flags=re.MULTILINE)
    # Collapse runs of 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse runs of 2+ spaces into 1
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _extract_fit_text(uploaded_file, pasted_text: str) -> str:
    """
    Pull plain text out of an uploaded fit-analysis file (PDF/DOCX/TXT) or fall
    back to pasted text. Returns "" on failure so the rest of the guide still
    generates cleanly.
    """
    pasted = (pasted_text or "").strip()
    if not uploaded_file:
        return pasted

    name = (uploaded_file.name or "").lower()
    try:
        data = uploaded_file.read()
    except Exception as e:
        logger.warning(f"Could not read uploaded fit file: {e}")
        return pasted

    text = ""
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        elif name.endswith(".docx"):
            import docx  # python-docx
            doc = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            # Treat as plain text — try utf-8, fall back to latin-1
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = data.decode("latin-1", errors="replace")
    except Exception as e:
        logger.warning(f"Could not parse fit file '{name}': {e}")
        text = ""

    # Combine parsed file text + any pasted text (pasted wins as supplement)
    combined = "\n\n".join(t for t in (text.strip(), pasted) if t)
    return combined


# Simple in-memory status tracker (same pattern as Resume Tool)
_generation_status = {}
_generation_lock = threading.Lock()


def _bullhorn_configured():
    """Check whether Bullhorn API credentials are set."""
    return bool(
        getattr(settings, "BULLHORN_CLIENT_ID", "")
        and getattr(settings, "BULLHORN_CLIENT_SECRET", "")
        and getattr(settings, "BULLHORN_API_USERNAME", "")
        and getattr(settings, "BULLHORN_API_PASSWORD", "")
    )


def index(request):
    """Main form page."""
    return render(request, "index.html", {
        "default_tips": "\n".join(DEFAULT_INTERVIEW_TIPS),
        "default_practices": "\n".join(GENERAL_TIPS),
        "default_followup": "\n".join(FOLLOW_UP_TIPS),
        "bullhorn_enabled": _bullhorn_configured(),
    })


def _parse_interviewers(post) -> list[dict]:
    """Pull 1..N interviewers from the form.

    Supports the new array-style fields (`interviewer_name_0`, `interviewer_name_1`, ...)
    used by the multi-interviewer UI, and falls back to the legacy single-interviewer
    field names (`interviewer_name`, etc.) if the arrayed ones aren't present.
    Blank rows (no name) are dropped.
    """
    interviewers: list[dict] = []
    # Scan for indexed fields 0..9 — UI caps at 5 but a little slack is cheap.
    for idx in range(10):
        name = (post.get(f"interviewer_name_{idx}", "") or "").strip()
        title = (post.get(f"interviewer_title_{idx}", "") or "").strip()
        linkedin = (post.get(f"interviewer_linkedin_{idx}", "") or "").strip()
        background = _clean_pasted_text(post.get(f"interviewer_background_{idx}", "") or "")
        custom_notes = _clean_pasted_text(post.get(f"interviewer_custom_notes_{idx}", "") or "")
        if name:
            interviewers.append({
                "name": name, "title": title, "linkedin": linkedin,
                "background": background, "custom_notes": custom_notes,
            })

    # Fallback: legacy single-interviewer field names
    if not interviewers:
        name = (post.get("interviewer_name", "") or "").strip()
        if name:
            interviewers.append({
                "name": name,
                "title": (post.get("interviewer_title", "") or "").strip(),
                "linkedin": (post.get("interviewer_linkedin", "") or "").strip(),
                "background": _clean_pasted_text(post.get("interviewer_background", "") or ""),
                "custom_notes": _clean_pasted_text(post.get("interviewer_custom_notes", "") or ""),
            })
    return interviewers


def _parse_selected_news(post) -> list[dict] | None:
    """Pull the recruiter-approved news items from the form.

    UI posts them as a JSON string in `selected_news_json`. If the field is
    empty or absent, returns None (meaning: fall back to auto-generating news,
    or — per new behavior — just skip news). Empty array `[]` is a distinct
    signal: "recruiter explicitly chose to include NO news — don't regenerate."
    """
    import json as _json
    raw = (post.get("selected_news_json", "") or "").strip()
    if not raw:
        return None
    try:
        parsed = _json.loads(raw)
        if not isinstance(parsed, list):
            return None
        cleaned = []
        for item in parsed[:3]:  # cap at 3 regardless
            if isinstance(item, dict) and item.get("headline"):
                cleaned.append({
                    "headline": str(item.get("headline", ""))[:200],
                    "summary": str(item.get("summary", ""))[:800],
                    "date": str(item.get("date", ""))[:40],
                    "relevance": str(item.get("relevance", ""))[:400],
                })
        return cleaned
    except (_json.JSONDecodeError, ValueError):
        return None


@require_http_methods(["POST"])
def generate_guide(request):
    """Accept form data, generate guide, return download link."""
    # Collect form inputs — _clean_pasted_text strips markdown artifacts,
    # smart quotes, bullet chars, and excess whitespace from free-text fields.
    _c = _clean_pasted_text
    form_data = {
        "candidate_name": request.POST.get("candidate_name", "").strip(),
        "job_title": request.POST.get("job_title", "").strip(),
        "job_description": _c(request.POST.get("job_description", "")),
        "health_system_name": request.POST.get("health_system_name", "").strip(),
        "health_system_info": _c(request.POST.get("health_system_info", "")),
        "health_system_website": request.POST.get("health_system_website", "").strip(),
        "health_system_address": request.POST.get("health_system_address", "").strip(),
        "interview_timezone": request.POST.get("interview_timezone", "CT"),
        # Legacy single-interviewer fields (kept for backward-compat — the
        # multi-interviewer list lives in `interviewers` below).
        "interviewer_name": request.POST.get("interviewer_name", "").strip(),
        "interviewer_title": request.POST.get("interviewer_title", "").strip(),
        "interviewer_linkedin": request.POST.get("interviewer_linkedin", "").strip(),
        "interviewer_background": _c(request.POST.get("interviewer_background", "")),
        "interview_date": request.POST.get("interview_date", "").strip(),
        "interview_time": request.POST.get("interview_time", "").strip(),
        "interview_format": request.POST.get("interview_format", "Video (Zoom/Teams)"),
        "interview_location": request.POST.get("interview_location", "").strip(),
        "contact_name": request.POST.get("contact_name", "").strip(),
        "contact_email": request.POST.get("contact_email", "").strip(),
        "contact_phone": request.POST.get("contact_phone", "").strip(),
        "interview_tips": _c(request.POST.get("interview_tips", "")),
        "best_practices": _c(request.POST.get("best_practices", "")),
        "follow_up_tips": _c(request.POST.get("follow_up_tips", "")),
    }

    # Validate required fields
    required = ["candidate_name", "job_title", "job_description", "health_system_name"]
    missing = [f for f in required if not form_data[f]]
    if missing:
        return render(request, "index.html", {
            "error": f"Please fill in: {', '.join(missing)}",
            "form_data": form_data,
            "default_tips": "\n".join(DEFAULT_INTERVIEW_TIPS),
            "default_practices": "\n".join(GENERAL_TIPS),
            "default_followup": "\n".join(FOLLOW_UP_TIPS),
            "bullhorn_enabled": _bullhorn_configured(),
        })

    # Pull fit-analysis text from uploaded file and/or pasted textarea
    fit_text = _clean_pasted_text(_extract_fit_text(
        request.FILES.get("fit_analysis_file"),
        request.POST.get("fit_analysis_text", ""),
    ))
    uploaded = request.FILES.get("fit_analysis_file")
    logger.info(
        f"fit_analysis: uploaded={uploaded.name if uploaded else None}, "
        f"pasted_chars={len((request.POST.get('fit_analysis_text') or '').strip())}, "
        f"extracted_chars={len(fit_text)}"
    )

    # Pull candidate resume text the same way (same helper — file or pasted textarea)
    resume_text = _clean_pasted_text(_extract_fit_text(
        request.FILES.get("candidate_resume_file"),
        request.POST.get("candidate_resume_text", ""),
    ))
    resume_uploaded = request.FILES.get("candidate_resume_file")
    logger.info(
        f"candidate_resume: uploaded={resume_uploaded.name if resume_uploaded else None}, "
        f"pasted_chars={len((request.POST.get('candidate_resume_text') or '').strip())}, "
        f"extracted_chars={len(resume_text)}"
    )

    # Parse multi-interviewer list (falls back to legacy single-interviewer fields)
    interviewers = _parse_interviewers(request.POST)
    logger.info(f"interviewers: {len(interviewers)} parsed")

    # Parse recruiter-approved news (None if she didn't preview — skip news in PDF)
    selected_news = _parse_selected_news(request.POST)
    logger.info(f"selected_news: {'none' if selected_news is None else f'{len(selected_news)} items'}")

    # Generate the guide content (AI + templates)
    guide_content = generate_interview_guide(
        form_data,
        fit_text=fit_text,
        resume_text=resume_text,
        interviewers=interviewers if interviewers else None,
        selected_news=selected_news,
    )

    # Serialize complex objects as JSON so the preview form can pass them back
    import json as _json
    interviewers_for_preview = guide_content.get('interviewers') or []
    fit_analysis = guide_content.get('fit_analysis') or {}
    recent_news = guide_content.get('recent_news') or []

    return render(request, "preview.html", {
        "form_data": form_data,
        "talking_points": guide_content.get('talking_points', []),
        "questions_to_ask": guide_content.get('questions_to_ask', []),
        "likely_questions": guide_content.get('likely_questions', []),
        "interviewers": interviewers_for_preview,
        "recent_news": recent_news,
        "fit_analysis": fit_analysis,
        # JSON blobs for hidden fields (pass-through to finalize)
        "selected_news_json": _json.dumps(recent_news),
        "interviewers_json": _json.dumps(interviewers_for_preview),
        "fit_analysis_json": _json.dumps(fit_analysis),
    })


@require_http_methods(["POST"])
def finalize_guide(request):
    """Accept edited content from the preview page, build the final PDF."""
    import json as _json

    # Reconstruct form_data from hidden fields
    form_data = {
        "candidate_name": request.POST.get("candidate_name", "").strip(),
        "job_title": request.POST.get("job_title", "").strip(),
        "job_description": request.POST.get("job_description", ""),
        "health_system_name": request.POST.get("health_system_name", "").strip(),
        "health_system_info": request.POST.get("health_system_info", ""),
        "health_system_website": request.POST.get("health_system_website", "").strip(),
        "health_system_address": request.POST.get("health_system_address", "").strip(),
        "interview_timezone": request.POST.get("interview_timezone", "CT"),
        "interviewer_name": "",
        "interviewer_title": "",
        "interviewer_linkedin": "",
        "interviewer_background": "",
        "interview_date": request.POST.get("interview_date", "").strip(),
        "interview_time": request.POST.get("interview_time", "").strip(),
        "interview_format": request.POST.get("interview_format", "Video (Zoom/Teams)"),
        "interview_location": request.POST.get("interview_location", "").strip(),
        "contact_name": request.POST.get("contact_name", "").strip(),
        "contact_email": request.POST.get("contact_email", "").strip(),
        "contact_phone": request.POST.get("contact_phone", "").strip(),
        "interview_tips": request.POST.get("interview_tips", ""),
        "best_practices": request.POST.get("best_practices", ""),
        "follow_up_tips": request.POST.get("follow_up_tips", ""),
    }

    # Read edited list fields (multiple values with same name)
    talking_points = [t.strip() for t in request.POST.getlist("talking_point") if t.strip()]
    questions_to_ask = [q.strip() for q in request.POST.getlist("question_to_ask") if q.strip()]
    likely_questions = [q.strip() for q in request.POST.getlist("likely_question") if q.strip()]
    fit_talking_points = [t.strip() for t in request.POST.getlist("fit_talking_point") if t.strip()]

    # Reconstruct interviewers with edited insights
    interviewers = []
    try:
        interviewers_raw = _json.loads(request.POST.get("interviewers_json", "[]"))
    except (_json.JSONDecodeError, ValueError):
        interviewers_raw = []
    for idx, iv in enumerate(interviewers_raw):
        edited_insights = request.POST.get(f"interviewer_insights_{idx}", iv.get("insights", ""))
        iv["insights"] = edited_insights.strip()
        # Also set custom_notes so the PDF builder uses the edited text verbatim
        iv["custom_notes"] = edited_insights.strip()
        interviewers.append(iv)

    # Reconstruct news from edited fields
    recent_news = []
    for idx in range(10):
        headline = request.POST.get(f"news_headline_{idx}", "").strip()
        if not headline:
            continue
        recent_news.append({
            "headline": headline,
            "summary": request.POST.get(f"news_summary_{idx}", "").strip(),
            "date": request.POST.get(f"news_date_{idx}", "").strip(),
            "relevance": request.POST.get(f"news_relevance_{idx}", "").strip(),
        })

    # Reconstruct fit analysis from edited fields
    fit_analysis = {}
    try:
        fit_raw = _json.loads(request.POST.get("fit_analysis_json", "{}"))
    except (_json.JSONDecodeError, ValueError):
        fit_raw = {}

    # Matched strengths — read edited values, fall back to original
    matched_strengths = []
    for idx in range(20):
        point = request.POST.get(f"fit_strength_point_{idx}", "").strip()
        evidence = request.POST.get(f"fit_strength_evidence_{idx}", "").strip()
        if point or evidence:
            matched_strengths.append({"point": point, "evidence": evidence})
    if matched_strengths:
        fit_analysis["matched_strengths"] = matched_strengths
    elif fit_raw.get("matched_strengths"):
        fit_analysis["matched_strengths"] = fit_raw["matched_strengths"]

    # Gaps
    gaps = []
    for idx in range(20):
        gap = request.POST.get(f"fit_gap_gap_{idx}", "").strip()
        framing = request.POST.get(f"fit_gap_framing_{idx}", "").strip()
        if gap or framing:
            gaps.append({"gap": gap, "framing": framing})
    if gaps:
        fit_analysis["gaps_to_address"] = gaps
    elif fit_raw.get("gaps_to_address"):
        fit_analysis["gaps_to_address"] = fit_raw["gaps_to_address"]

    # Fit talking points (edited list)
    if fit_talking_points:
        fit_analysis["suggested_talking_points"] = fit_talking_points
    elif fit_raw.get("suggested_talking_points"):
        fit_analysis["suggested_talking_points"] = fit_raw["suggested_talking_points"]

    # Story prompts
    story_prompts = []
    for idx in range(20):
        prompt = request.POST.get(f"fit_story_prompt_{idx}", "").strip()
        situation = request.POST.get(f"fit_story_situation_{idx}", "").strip()
        if prompt or situation:
            story_prompts.append({"prompt": prompt, "situation": situation})
    if story_prompts:
        fit_analysis["story_prompts"] = story_prompts
    elif fit_raw.get("story_prompts"):
        fit_analysis["story_prompts"] = fit_raw["story_prompts"]

    # Assemble guide_content for the PDF builder
    guide_content = {
        "talking_points": talking_points,
        "questions_to_ask": questions_to_ask,
        "likely_questions": likely_questions,
        "interviewer_insights": interviewers[0]["insights"] if interviewers else "",
        "interviewers": interviewers,
        "recent_news": recent_news,
        "fit_analysis": fit_analysis,
        "general_tips": GENERAL_TIPS,
        "interview_tips": [t.strip() for t in form_data.get("interview_tips", "").splitlines() if t.strip()] or list(DEFAULT_INTERVIEW_TIPS),
        "follow_up_tips": [t.strip() for t in form_data.get("follow_up_tips", "").splitlines() if t.strip()] or list(FOLLOW_UP_TIPS),
        "day_of_checklist": [],  # included via Before the Interview cards, not a list
    }

    # Build the PDF
    guide_id = str(uuid.uuid4())[:8]
    safe_name = form_data["candidate_name"].replace(" ", "_")
    filename = f"Interview_Guide_{safe_name}_{guide_id}.pdf"
    buffer = io.BytesIO()
    build_guide_pdf(guide_content, form_data, buffer)
    buffer.seek(0)

    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-store"
    return response


@require_http_methods(["POST"])
def fetch_news(request):
    """AJAX endpoint: fetch recent news for a health system (6mo filter, max 3)."""
    import json
    try:
        body = json.loads(request.body)
        health_system_name = body.get("health_system_name", "").strip()
    except (json.JSONDecodeError, AttributeError):
        health_system_name = request.POST.get("health_system_name", "").strip()

    if not health_system_name:
        return JsonResponse({"news": [], "error": "No health system name provided."})

    news = _generate_recent_news({"health_system_name": health_system_name})
    return JsonResponse({"news": news})


@require_http_methods(["POST"])
def fetch_interviewer_notes(request):
    """AJAX endpoint: AI-draft notes about a single interviewer so Rachel can
    preview + edit before sending through to the PDF generator."""
    import json
    from guide_generator.generator import _generate_interviewer_insights

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    interviewer = {
        "name": (body.get("name") or "").strip(),
        "title": (body.get("title") or "").strip(),
        "linkedin": (body.get("linkedin") or "").strip(),
        "background": (body.get("background") or "").strip(),
    }
    if not interviewer["name"]:
        return JsonResponse({"ok": False, "error": "Interviewer name required."})

    # Minimal form context — the generator only needs health_system_name + job_title.
    form_context = {
        "health_system_name": (body.get("health_system_name") or "").strip(),
        "job_title": (body.get("job_title") or "").strip(),
    }

    try:
        notes = _generate_interviewer_insights(form_context, interviewer)
        return JsonResponse({"ok": True, "notes": notes or ""})
    except Exception:
        logger.exception("fetch_interviewer_notes failed")
        return JsonResponse({"ok": False, "error": "Could not draft interviewer notes."}, status=500)


# -- Bullhorn API endpoints ------------------------------------------------

def bullhorn_candidate_search(request):
    """AJAX endpoint to search Bullhorn candidates by name."""
    import logging
    logger = logging.getLogger(__name__)

    query = request.GET.get("q", "").strip()
    candidate_id = request.GET.get("id", "").strip()

    if not _bullhorn_configured():
        return JsonResponse({"ok": False, "error": "Bullhorn not configured."}, status=500)

    try:
        from core.bullhorn import search_candidates, get_candidate
        if candidate_id:
            candidate = get_candidate(int(candidate_id))
            return JsonResponse({"ok": True, "candidate": candidate})
        elif query and len(query) >= 2:
            results = search_candidates(query)
            return JsonResponse({"ok": True, "results": results})
        else:
            return JsonResponse({"ok": True, "results": []})
    except Exception:
        logger.exception("Bullhorn candidate search failed")
        return JsonResponse(
            {"ok": False, "error": "Could not search Bullhorn candidates."},
            status=500,
        )


def bullhorn_job_search(request):
    """AJAX endpoint to search Bullhorn job orders by title/keyword."""
    import logging
    logger = logging.getLogger(__name__)

    query = request.GET.get("q", "").strip()
    job_id = request.GET.get("id", "").strip()

    if not _bullhorn_configured():
        return JsonResponse({"ok": False, "error": "Bullhorn not configured."}, status=500)

    try:
        from core.bullhorn import search_job_orders, get_job_order
        if job_id:
            jo = get_job_order(int(job_id))
            return JsonResponse({"ok": True, "job_order": jo})
        elif query and len(query) >= 2:
            results = search_job_orders(query)
            return JsonResponse({"ok": True, "results": results})
        else:
            return JsonResponse({"ok": True, "results": []})
    except Exception:
        logger.exception("Bullhorn job order search failed")
        return JsonResponse(
            {"ok": False, "error": "Could not search Bullhorn job orders."},
            status=500,
        )


def download_guide(request, filename):
    """Serve the generated PDF for download."""
    filepath = settings.GUIDES_DIR / filename
    if not filepath.exists():
        raise Http404("Guide not found.")
    response = FileResponse(
        open(filepath, "rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
def debug_claude(request):
    """Diagnostic endpoint: check if Claude API is actually working."""
    import time
    from guide_generator import generator as gen

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    result = {
        'has_api_key': bool(api_key),
        'api_key_length': len(api_key),
        'api_key_prefix': api_key[:10] + '...' if api_key else '',
        'model_in_use': 'claude-sonnet-4-6',
    }

    if not api_key:
        result['test_call'] = 'skipped — no key'
        return JsonResponse(result)

    t0 = time.time()
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=50,
            messages=[{'role': 'user', 'content': 'Reply with exactly: PING'}],
        )
        result['test_call'] = msg.content[0].text
        result['elapsed_sec'] = round(time.time() - t0, 2)
    except Exception as e:
        result['test_call_error'] = f'{type(e).__name__}: {e}'
        result['elapsed_sec'] = round(time.time() - t0, 2)

    logger.error(f'[debug_claude] {result}')
    return JsonResponse(result)
