"""
Interview Guide Generator — hybrid AI + template approach.

AI-generated sections:
  - Tailored talking points based on job description
  - Questions the candidate should ask the interviewer
  - Key themes to emphasize based on the role

Template sections:
  - General interview best practices
  - Day-of logistics checklist
  - Follow-up guidance
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ─── TEMPLATE CONTENT (no AI needed) ────────────────────────────────────

DEFAULT_INTERVIEW_TIPS = [
    "Test your technology (video, audio, internet connection) at least 30 minutes before the interview.",
    "Dress business casual — when in doubt, overdress rather than underdress.",
    "Have your resume printed or pulled up somewhere easy to reference during the conversation.",
    "Sign into the meeting or arrive at the location a few minutes early.",
    "Keep a glass of water and a notepad nearby.",
    "Silence your phone completely before the interview starts.",
    "Prepare 2–3 specific examples of your work that demonstrate relevant experience and measurable results.",
    "Research the organization beforehand — review their website, recent news, and mission statement.",
    "Make eye contact, smile, and address the interviewer by name.",
    "Be honest about what you don't know, but frame it positively and show willingness to learn.",
]

GENERAL_TIPS = [
    "Research the organization thoroughly before the interview — review their website, recent news, mission statement, and any publicly available strategic plans.",
    "Sign into the meeting 5–10 minutes early. Test your audio, video, and internet connection 30 minutes beforehand, and have a backup plan (phone dial-in number) ready in case something fails.",
    "Dress professionally from the waist up — business formal unless told otherwise. When in doubt, overdress rather than underdress.",
    "Have your resume and a list of references pulled up on your screen or printed nearby so you can reference them if asked. Keep a notepad and pen handy for notes.",
    "Prepare 2–3 concise stories that demonstrate your relevant experience, focusing on the situation, your actions, and the measurable results you achieved.",
    "Look into the camera (not the screen) when speaking, smile, and address each interviewer by name.",
    "Listen carefully to each question. It's perfectly fine to pause briefly before answering — it shows thoughtfulness.",
    "Be honest about what you don't know, but frame it positively: 'I haven't worked with that specific module, but I've done X, which is similar, and I'm a fast learner.'",
    "Show enthusiasm for the role and the organization. Interviewers want to see genuine interest, not just qualifications.",
    "Avoid speaking negatively about previous employers, colleagues, or clients.",
]

FOLLOW_UP_TIPS = [
    "Write a personalized thank-you note within 24 hours of the interview and send it to your Anura Connect recruiter — we'll pass it along to the hiring manager on your behalf.",
    "Reference something specific from your conversation to make it memorable.",
    "Reiterate your interest in the role and briefly mention why you'd be a great fit.",
    "If you discussed any follow-up items (articles, references, portfolio samples), include them in your note.",
    "Contact your recruiter at Anura Connect after the interview to share how it went — this helps us advocate for you.",
]

DAY_OF_CHECKLIST = [
    "Confirm the interview time and the meeting link or dial-in details. Most interviews are conducted remotely via video.",
    "Test your internet, camera, and microphone. Close unnecessary browser tabs and apps before the meeting starts.",
    "Choose a quiet, well-lit space with a clean background. Natural light facing you works best.",
    "If the interview is in-person (rare): look up the address, parking situation, and building entrance ahead of time.",
    "Have a glass of water nearby.",
    "Silence your phone completely.",
    "Keep your interview guide and notes within easy reach (but don't read from them verbatim).",
    "Take a few deep breaths before the interview starts — confidence comes from preparation, and you've done the work.",
]


# ─── AI-GENERATED CONTENT ───────────────────────────────────────────────

def _call_claude_with_search(prompt: str) -> str:
    """Call Anthropic API with web search enabled for real-time news.

    Does NOT fall back to a second Claude call on failure — that would chain
    two sequential timeouts and blow past Railway's 30s edge limit.
    """
    if not ANTHROPIC_API_KEY:
        logger.error("No ANTHROPIC_API_KEY set — skipping AI generation.")
        return ""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=15.0)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract text from response (may include tool use blocks)
        text_parts = []
        for block in message.content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
        return "\n".join(text_parts) if text_parts else ""
    except Exception as e:
        logger.error(f"Claude API call with search failed: {e}")
        return ""


def _call_claude(prompt: str) -> str:
    """Call Anthropic API for AI-generated content. Falls back to empty string on failure."""
    if not ANTHROPIC_API_KEY:
        logger.error("No ANTHROPIC_API_KEY set — skipping AI generation.")
        return ""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=15.0)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return ""


def _generate_talking_points(form_data: dict, fit_text: str = "", resume_text: str = "") -> list[str]:
    """AI-generated talking points tailored to the role and health system."""
    fit_block = f"\n\nRecruiter's Candidate Fit Notes (use these to pick which strengths to surface and which gaps to frame):\n{fit_text.strip()[:3500]}" if fit_text and fit_text.strip() else ""
    resume_block = f"\n\nCandidate's Resume (use this to ground talking points in what the candidate has actually done — named modules, employers, projects, certifications):\n{resume_text.strip()[:4000]}" if resume_text and resume_text.strip() else ""
    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}
Job Description:
{form_data['job_description']}

{f"Interviewer: {form_data['interviewer_name']}, {form_data['interviewer_title']}" if form_data.get('interviewer_name') else ""}
{f"Interviewer Background: {form_data['interviewer_background']}" if form_data.get('interviewer_background') else ""}
{f"Health System Context: {form_data['health_system_info']}" if form_data.get('health_system_info') else ""}{fit_block}{resume_block}

Generate 3-5 specific talking points this candidate should weave into their interview answers.

IMPORTANT: Use these inputs in priority order when shaping talking points:
1. "Recruiter's Candidate Fit Notes" (if provided) — PRIMARY signal. Surface the specific strengths the recruiter called out, proactively frame the gaps/concerns the recruiter flagged, and tie each back to what this role and health system actually need. Name things concretely, not generically.
2. "Candidate's Resume" (if provided) — ground every talking point in something the candidate has actually done. Reference specific employers, Epic modules, projects, certifications, or outcomes from the resume. Do not invent experience.
3. Job description — use to judge which resume bullets/strengths are most relevant to this role.

If neither fit notes nor resume are provided, fall back to reasoning from the job description alone.

Each point should:
- Be directly relevant to the job description and health system
- Reference specific skills, modules, or experience areas the candidate should highlight
- Be actionable and concrete (not generic advice)

Return ONLY a JSON array of strings. No markdown, no explanation. Example:
["Point one here.", "Point two here."]"""

    result = _call_claude(prompt)
    if result:
        try:
            # Try to parse JSON from the response
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.error("Could not parse AI talking points, using fallback.")

    # Fallback if AI fails
    return [
        f"Highlight your experience with the specific Epic modules or technical skills mentioned in the job description for {form_data['job_title']}.",
        f"Demonstrate your understanding of {form_data['health_system_name']}'s environment and how your skills align with their needs.",
        "Share examples of successful go-lives, optimizations, or implementations you've led.",
        "Emphasize your ability to work collaboratively with clinical end-users and translate technical concepts for non-technical stakeholders.",
    ]


def _generate_questions_to_ask(form_data: dict) -> list[str]:
    """AI-generated questions the candidate should ask the interviewer."""
    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}
Job Description:
{form_data['job_description']}

{f"Interviewer: {form_data['interviewer_name']}, {form_data['interviewer_title']}" if form_data.get('interviewer_name') else ""}
{f"Health System Context: {form_data['health_system_info']}" if form_data.get('health_system_info') else ""}

Generate 3-5 thoughtful questions the candidate should ask the interviewer. These should:
- Show the candidate has done their homework on the health system and role
- Demonstrate strategic thinking about the position
- Help the candidate evaluate fit
- Be tailored to the interviewer's role/title if provided
- NOT be questions easily answered by the job description itself

Return ONLY a JSON array of strings. No markdown, no explanation."""

    result = _call_claude(prompt)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.error("Could not parse AI questions, using fallback.")

    return [
        "What does a typical day look like in this role?",
        "What are the biggest challenges the team is currently facing?",
        f"What are {form_data['health_system_name']}'s top IT priorities for the next 12 months?",
        "How do you measure success for someone in this position?",
    ]


def _generate_interviewer_insights(form_data: dict, interviewer: dict | None = None) -> str:
    """AI-generated insights about ONE interviewer based on provided info.

    If `interviewer` is passed, uses those fields (for multi-interviewer support).
    Otherwise falls back to the legacy single-interviewer fields on form_data.
    """
    if interviewer is None:
        interviewer = {
            "name": form_data.get("interviewer_name", ""),
            "title": form_data.get("interviewer_title", ""),
            "linkedin": form_data.get("interviewer_linkedin", ""),
            "background": form_data.get("interviewer_background", ""),
        }
    if not (interviewer.get("name") or "").strip():
        return ""

    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

The candidate will be interviewing with:
Name: {interviewer.get('name', '')}
Title: {interviewer.get('title') or 'Not provided'}
LinkedIn: {interviewer.get('linkedin') or 'Not provided'}
Background notes: {interviewer.get('background') or 'Not provided'}

Health System: {form_data['health_system_name']}
Role being interviewed for: {form_data['job_title']}

Write a concise 2-3 sentence summary covering: what this person likely cares about given their role, and one tip for connecting with them in the interview.

Keep it tight and actionable. No fluff. Do NOT invent biographical details — only work with what's provided. If little info is given, focus on what their title tells us about their perspective."""

    result = _call_claude(prompt)
    return result if result else ""


def _generate_likely_questions(form_data: dict, fit_text: str = "", resume_text: str = "") -> list[str]:
    """AI-generated questions the interviewer is likely to ask, so the candidate can prepare.

    Priority: ground questions in the resume ↔ job-description match. Interviewer
    background is flavor, not the main driver — the recruiter fed it back to us
    because too many questions were leaning on it.
    """
    fit_block = f"\n\nRecruiter's Candidate Fit Notes (supplementary — use to reinforce strengths/gaps the recruiter has already identified):\n{fit_text.strip()[:3500]}" if fit_text and fit_text.strip() else ""
    resume_block = f"\n\nCandidate's Resume (PRIMARY source of truth for the candidate's background):\n{resume_text.strip()[:4000]}" if resume_text and resume_text.strip() else ""
    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}
Job Description:
{form_data['job_description']}
{resume_block}{fit_block}

{f"(Interviewer is {form_data['interviewer_name']}, {form_data['interviewer_title']} — useful flavor but DO NOT let it dominate the questions.)" if form_data.get('interviewer_name') else ""}

Generate 3-5 questions the interviewer is likely to ask the candidate.

PRIORITY ORDER — follow strictly:
1. **Resume ↔ Job Description match** (PRIMARY). For each major requirement in the JD, ask the question an interviewer would most naturally ask to test whether the candidate has genuinely done that thing. Anchor each question in a specific item on the candidate's resume: a named module, employer, project, outcome, certification, or date. "Walk me through your Cadence template redesign at [employer]" is great; "Tell me about your experience" is not.
2. **JD-only questions** where the resume doesn't obviously cover a requirement — ask the question that would give the candidate a chance to address that gap.
3. **Recruiter's fit notes** (if provided) — use to reinforce 1-2 questions around the specific strengths or gaps the recruiter already flagged.
4. **Interviewer background** — flavor only. Do NOT generate questions just because of who the interviewer is. The questions this role would ask are driven by the role, not the person. At most one question may lean into the interviewer's perspective.

Include a mix of:
- Resume-grounded technical questions that map to JD requirements (MOST of the questions)
- 1 behavioral question tied to outcomes on the resume
- 1 situational question about a healthcare-IT scenario relevant to the JD

For each question, add a brief one-sentence tip in parentheses on how to approach the answer. Tips should reference the specific resume item the candidate should use in their answer whenever possible. Do NOT reference the STAR method or any specific interview framework.

Return ONLY a JSON array of strings. No markdown, no explanation. Example:
["Walk me through the Cadence template redesign you led at Advocate Aurora — what were the specific changes and what was the measured impact? (Tip: Quantify the 18% no-show reduction and name the clinics, don't generalize.)"]"""

    result = _call_claude(prompt)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.error("Could not parse AI likely questions, using fallback.")

    return [
        f"Tell me about your experience with the technologies mentioned in the {form_data['job_title']} job description. (Tip: Be specific — name the modules, tools, or systems you've worked with.)",
        "Describe a challenging go-live or system implementation you supported. What was your role and how did you handle obstacles? (Tip: Walk through the situation, your specific actions, and the measurable outcome.)",
        f"Why are you interested in working at {form_data['health_system_name']}? (Tip: Reference something specific about the organization — their mission, recent initiatives, or growth.)",
        "How do you handle pushback from clinical end-users during a system change or workflow update? (Tip: Show empathy for the user's perspective while explaining how you drive adoption.)",
    ]


def _generate_fit_analysis(form_data: dict, fit_text: str) -> dict:
    """
    AI-structured candidate-fit analysis based on an uploaded/pasted fit document.

    Returns a dict with four keys:
      - matched_strengths:       list of {"point": str, "evidence": str}
      - gaps_to_address:         list of {"gap": str, "framing": str}
      - suggested_talking_points: list[str]
      - story_prompts:           list of {"prompt": str, "situation": str}

    If no fit_text is provided, returns an empty dict (caller should skip the section).
    """
    if not fit_text or not fit_text.strip():
        return {}

    # Keep the prompt payload bounded — fit docs are typically 1–3 pages of text.
    fit_excerpt = fit_text.strip()
    if len(fit_excerpt) > 12000:
        fit_excerpt = fit_excerpt[:12000] + "\n\n[...truncated for length...]"

    prompt = f"""You are helping a healthcare IT consultant prepare for an interview.

A recruiter has already prepared a "candidate fit analysis" — notes on how this candidate's background aligns with the role. Your job is to restructure and sharpen that analysis into a section the candidate will read before the interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}

Job Description:
{form_data['job_description']}

Recruiter's Fit Analysis (source material):
\"\"\"
{fit_excerpt}
\"\"\"

Produce a JSON object with exactly these four keys:

1. "matched_strengths": an array of 4–6 objects, each with:
   - "point":    a short (<=10 word) headline naming the strength (e.g., "Epic Ambulatory go-live leadership")
   - "evidence": a 1–2 sentence specific example from their background that proves it, phrased in second person ("You led the go-live at...")

2. "gaps_to_address": an array of 2–4 objects, each with:
   - "gap":     a short (<=10 word) headline naming an area where the candidate is lighter than the JD asks for
   - "framing": 1–2 sentences of coaching on how to honestly frame it — what adjacent experience to pivot to, what learning posture to show. Never recommend bluffing.

3. "suggested_talking_points": an array of 4–6 ready-to-say sentences the candidate can weave into answers. Each should connect a specific piece of their background to a specific requirement from the JD. Write them as the candidate would say them, in first person.

4. "story_prompts": an array of 3–5 objects, each with:
   - "prompt":    a likely interview question this candidate is well-positioned to answer (e.g., "Tell me about a time you led a go-live under pressure.")
   - "situation": 1–2 sentences pointing to the specific situation from their background they should use, written in second person ("Use the {{project}} go-live where...")

Rules:
- Only use facts present in the recruiter's fit analysis or derivable from the job description. Do NOT invent experience.
- Be specific. Prefer concrete projects, systems, modules, and outcomes over generic adjectives.
- Keep each text field under ~250 characters.
- Return ONLY the JSON object. No markdown fences, no preamble."""

    result = _call_claude(prompt)
    if not result:
        return {}

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(cleaned)
        # Normalize — ensure every key exists with a safe default
        return {
            "matched_strengths": parsed.get("matched_strengths", []) or [],
            "gaps_to_address": parsed.get("gaps_to_address", []) or [],
            "suggested_talking_points": parsed.get("suggested_talking_points", []) or [],
            "story_prompts": parsed.get("story_prompts", []) or [],
        }
    except (json.JSONDecodeError, IndexError, KeyError, AttributeError) as e:
        logger.warning(f"Could not parse AI fit analysis: {e}")
        return {}


def _generate_recent_news(form_data: dict) -> list[dict]:
    """AI-generated recent news about the health system using web search.

    Constrained to news from the last 6 months and capped at 3 items — the
    recruiter previews these before they land in the PDF, so fewer, fresher
    items beat a long stale list.
    """
    from datetime import date, timedelta
    today = date.today()
    cutoff = today - timedelta(days=183)  # ~6 months
    prompt = f"""Search for recent news about {form_data['health_system_name']} health system.

STRICT DATE FILTER: Only include news items published on or after {cutoff.isoformat()} (the last 6 months, as of {today.isoformat()}).
Do NOT include anything older than {cutoff.isoformat()}, even if it's well-known or commonly cited. If you can't confirm the publication date is within the last 6 months, omit that item.

Focus on:
- Recent organizational changes, expansions, or mergers
- Technology implementations (especially Epic/EHR-related)
- Awards, recognitions, or rankings
- New facilities, services, or partnerships
- Leadership changes
- Financial news or strategic initiatives

Return AT MOST 3 news items (fewer is fine — prefer quality over quantity).
Each item should have:
- "headline": A concise headline (under 100 characters)
- "summary": A 1-2 sentence summary of the news
- "date": Specific publication date in "Month YYYY" form (e.g. "February 2026"). If you can't pin down the date to within 6 months, DO NOT include the item.
- "relevance": One sentence on why this matters for someone interviewing there

Example format:
[{{"headline": "Example Health Expands Epic Implementation", "summary": "Example Health announced...", "date": "February 2026", "relevance": "Shows the organization is investing in Epic, relevant for IT roles."}}]

Return ONLY the JSON array (max 3 items). No markdown, no explanation."""

    result = _call_claude_with_search(prompt)
    if result:
        try:
            cleaned = result.strip()
            # Try to extract JSON from the response
            if "```" in cleaned:
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            # Find the JSON array in the response
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            if start >= 0 and end > start:
                cleaned = cleaned[start:end]
            parsed = json.loads(cleaned)
            # Hard cap at 3 in case the model overshoots.
            return parsed[:3] if isinstance(parsed, list) else []
        except (json.JSONDecodeError, IndexError):
            logger.warning("Could not parse AI news results, using fallback.")

    # Fallback — return empty list (no news available)
    return []


# ─── MAIN GENERATOR ─────────────────────────────────────────────────────

def generate_interview_guide(
    form_data: dict,
    fit_text: str = "",
    resume_text: str = "",
    interviewers: list[dict] | None = None,
    selected_news: list[dict] | None = None,
) -> dict:
    """
    Generate the full interview guide content.
    Returns a dict with all sections ready for PDF rendering.

    fit_text: optional text of the recruiter's candidate fit analysis. If provided,
              a structured "Why You're a Fit" section is generated.
    interviewers: optional list of interviewer dicts, each with keys name/title/linkedin/background/custom_notes.
              If omitted, falls back to the legacy single-interviewer fields on form_data.
    selected_news: optional list of news item dicts the recruiter already previewed and approved.
              If provided, we use those verbatim and SKIP the news-generation call entirely
              (keeps news out of the 25s critical path).
    """
    # Normalize interviewers — fall back to legacy single-interviewer form_data fields.
    if interviewers is None:
        legacy = {
            "name": form_data.get("interviewer_name", ""),
            "title": form_data.get("interviewer_title", ""),
            "linkedin": form_data.get("interviewer_linkedin", ""),
            "background": form_data.get("interviewer_background", ""),
            "custom_notes": "",
        }
        interviewers = [legacy] if (legacy["name"] or "").strip() else []

    # Drop interviewers without a name; cap at 5 so the fan-out stays bounded.
    interviewers = [i for i in interviewers if (i.get("name") or "").strip()][:5]

    # Run Claude calls concurrently with a SHARED 25s deadline. If the whole
    # batch doesn't finish in 25s, any unfinished future falls back to its
    # default return value. This keeps wall-clock under Railway's 30s.
    from concurrent.futures import ThreadPoolExecutor
    import time as _time
    _t0 = _time.time()
    _DEADLINE = 25  # total seconds for the whole parallel phase

    # Max parallel workers: 5 core calls + up to 5 per-interviewer insight calls
    # (news is skipped when recruiter pre-selected items, so not counted here).
    _ex = ThreadPoolExecutor(max_workers=10)
    try:
        futures: dict[str, tuple] = {
            "talking_points":   (_ex.submit(_generate_talking_points,   form_data, fit_text, resume_text), []),
            "questions_to_ask": (_ex.submit(_generate_questions_to_ask, form_data), []),
            "likely_questions": (_ex.submit(_generate_likely_questions, form_data, fit_text, resume_text), []),
            "fit_analysis":     (_ex.submit(_generate_fit_analysis,     form_data, fit_text), {}),
        }

        # Per-interviewer insights — skip ones that have custom_notes already
        # (recruiter already edited, no need to spend a Claude call on them).
        insight_labels = []
        for idx, iv in enumerate(interviewers):
            if (iv.get("custom_notes") or "").strip():
                continue  # will use custom_notes verbatim; no Claude call needed
            label = f"interviewer_insights_{idx}"
            insight_labels.append((idx, label))
            futures[label] = (_ex.submit(_generate_interviewer_insights, form_data, iv), "")

        # News: only regenerate if recruiter didn't already preview-and-select.
        if selected_news is None:
            futures["recent_news"] = (_ex.submit(_generate_recent_news, form_data), [])

        def _remaining():
            return max(0.1, _DEADLINE - (_time.time() - _t0))

        results = {}
        for label, (fut, default) in futures.items():
            try:
                results[label] = fut.result(timeout=_remaining())
                logger.error(f"[{label}] ok at t={round(_time.time()-_t0,2)}s")
            except Exception as e:
                logger.error(f"[{label}] {type(e).__name__} at t={round(_time.time()-_t0,2)}s — fallback")
                results[label] = default

        talking_points   = results["talking_points"][:5]
        questions_to_ask = results["questions_to_ask"][:5]
        likely_questions = results["likely_questions"][:5]
        fit_analysis     = results["fit_analysis"]

        # Attach each interviewer's insights (custom_notes wins if present)
        for iv in interviewers:
            iv["insights"] = (iv.get("custom_notes") or "").strip()
        for idx, label in insight_labels:
            interviewers[idx]["insights"] = results.get(label, "") or ""

        # News: selected_news takes priority; else use generated; else empty.
        if selected_news is not None:
            recent_news = selected_news[:3]
        else:
            recent_news = results.get("recent_news", [])
    finally:
        # Fire-and-forget any stragglers — we're past the deadline.
        _ex.shutdown(wait=False, cancel_futures=True)
    logger.error(f"[generate_interview_guide] done in {round(_time.time()-_t0,2)}s")

    # Back-compat: keep the old single-interviewer "interviewer_insights" key
    # populated with the first interviewer's insights so any legacy callers /
    # templates don't break.
    interviewer_insights = interviewers[0]["insights"] if interviewers else ""

    # Use custom interview tips from form if provided, otherwise defaults
    custom_tips_text = form_data.get("interview_tips", "").strip()
    if custom_tips_text:
        interview_tips = [
            line.strip() for line in custom_tips_text.splitlines()
            if line.strip()
        ]
    else:
        interview_tips = list(DEFAULT_INTERVIEW_TIPS)

    # Use custom best practices from form if provided, otherwise defaults
    custom_practices_text = form_data.get("best_practices", "").strip()
    if custom_practices_text:
        general_tips = [
            line.strip() for line in custom_practices_text.splitlines()
            if line.strip()
        ]
    else:
        general_tips = list(GENERAL_TIPS)

    # Use custom follow-up tips from form if provided, otherwise defaults
    custom_followup_text = form_data.get("follow_up_tips", "").strip()
    if custom_followup_text:
        follow_up_tips = [
            line.strip() for line in custom_followup_text.splitlines()
            if line.strip()
        ]
    else:
        follow_up_tips = list(FOLLOW_UP_TIPS)

    return {
        "talking_points": talking_points,
        "questions_to_ask": questions_to_ask,
        "likely_questions": likely_questions,
        "interviewer_insights": interviewer_insights,  # legacy single-interviewer (back-compat)
        "interviewers": interviewers,                  # new: list of {name,title,linkedin,background,insights}
        "recent_news": recent_news,
        "fit_analysis": fit_analysis,
        "general_tips": GENERAL_TIPS,
        "interview_tips": interview_tips,
        "follow_up_tips": FOLLOW_UP_TIPS,
        "day_of_checklist": DAY_OF_CHECKLIST,
    }
