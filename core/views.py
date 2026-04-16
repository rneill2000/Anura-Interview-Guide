import os
import uuid
import threading
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from guide_generator.generator import generate_interview_guide, DEFAULT_INTERVIEW_TIPS, GENERAL_TIPS, FOLLOW_UP_TIPS, _generate_recent_news
from guide_generator.pdf_builder import build_guide_pdf


# Simple in-memory status tracker (same pattern as Resume Tool)
_generation_status = {}
_generation_lock = threading.Lock()


def _bullhorn_configured():
    """Check whether Bullhorn API credentials are set."""
    return bool(
        getattr(settings, "BULLHORN_CLIENT_ID", "")
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


@require_http_methods(["POST"])
def generate_guide(request):
    """Accept form data, generate guide, return download link."""
    # Collect form inputs
    form_data = {
        "candidate_name": request.POST.get("candidate_name", "").strip(),
        "job_title": request.POST.get("job_title", "").strip(),
        "job_description": request.POST.get("job_description", "").strip(),
        "health_system_name": request.POST.get("health_system_name", "").strip(),
        "health_system_info": request.POST.get("health_system_info", "").strip(),
        "interviewer_name": request.POST.get("interviewer_name", "").strip(),
        "interviewer_title": request.POST.get("interviewer_title", "").strip(),
        "interviewer_linkedin": request.POST.get("interviewer_linkedin", "").strip(),
        "interviewer_background": request.POST.get("interviewer_background", "").strip(),
        "interview_date": request.POST.get("interview_date", "").strip(),
        "interview_time": request.POST.get("interview_time", "").strip(),
        "interview_format": request.POST.get("interview_format", "In-Person"),
        "interview_location": request.POST.get("interview_location", "").strip(),
        "contact_name": request.POST.get("contact_name", "").strip(),
        "contact_email": request.POST.get("contact_email", "").strip(),
        "contact_phone": request.POST.get("contact_phone", "").strip(),
        "interview_tips": request.POST.get("interview_tips", "").strip(),
        "best_practices": request.POST.get("best_practices", "").strip(),
        "follow_up_tips": request.POST.get("follow_up_tips", "").strip(),
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

    # Generate unique ID for this guide
    guide_id = str(uuid.uuid4())[:8]

    # Generate the guide content (AI + templates)
    guide_content = generate_interview_guide(form_data)

    # Build the PDF
    safe_name = form_data["candidate_name"].replace(" ", "_")
    filename = f"Interview_Guide_{safe_name}_{guide_id}.pdf"
    filepath = settings.GUIDES_DIR / filename
    build_guide_pdf(guide_content, form_data, filepath)

    return render(request, "success.html", {
        "filename": filename,
        "candidate_name": form_data["candidate_name"],
        "job_title": form_data["job_title"],
        "health_system_name": form_data["health_system_name"],
    })


@require_http_methods(["POST"])
def fetch_news(request):
    """AJAX endpoint: fetch recent news for a health system."""
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
    return FileResponse(
        open(filepath, "rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
