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
    "Prepare 2–3 specific examples of your work using the STAR method (Situation, Task, Action, Result).",
    "Research the organization beforehand — review their website, recent news, and mission statement.",
    "Make eye contact, smile, and address the interviewer by name.",
    "Be honest about what you don't know, but frame it positively and show willingness to learn.",
]

GENERAL_TIPS = [
    "Research the organization thoroughly before the interview — review their website, recent news, mission statement, and any publicly available strategic plans.",
    "Sign into the meeting 5–10 minutes early. Test your audio, video, and internet connection 30 minutes beforehand, and have a backup plan (phone dial-in number) ready in case something fails.",
    "Dress professionally from the waist up — business formal unless told otherwise. When in doubt, overdress rather than underdress.",
    "Have your resume and a list of references pulled up on your screen or printed nearby so you can reference them if asked. Keep a notepad and pen handy for notes.",
    "Prepare 2–3 concise stories using the STAR method (Situation, Task, Action, Result) that demonstrate your relevant experience.",
    "Look into the camera (not the screen) when speaking, smile, and address each interviewer by name.",
    "Listen carefully to each question. It's perfectly fine to pause briefly before answering — it shows thoughtfulness.",
    "Be honest about what you don't know, but frame it positively: 'I haven't worked with that specific module, but I've done X, which is similar, and I'm a fast learner.'",
    "Show enthusiasm for the role and the organization. Interviewers want to see genuine interest, not just qualifications.",
    "Avoid speaking negatively about previous employers, colleagues, or clients.",
]

FOLLOW_UP_TIPS = [
    "Send a personalized thank-you email within 24 hours of the interview to each person you met with.",
    "Reference something specific from your conversation to make it memorable.",
    "Reiterate your interest in the role and briefly mention why you'd be a great fit.",
    "If you discussed any follow-up items (articles, references, portfolio samples), include them in your email.",
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

def _call_claude(prompt: str) -> str:
    """Call Anthropic API for AI-generated content. Falls back to empty string on failure."""
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set — skipping AI generation.")
        return ""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return ""


def _generate_talking_points(form_data: dict) -> list[str]:
    """AI-generated talking points tailored to the role and health system."""
    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}
Job Description:
{form_data['job_description']}

{f"Interviewer: {form_data['interviewer_name']}, {form_data['interviewer_title']}" if form_data.get('interviewer_name') else ""}
{f"Interviewer Background: {form_data['interviewer_background']}" if form_data.get('interviewer_background') else ""}
{f"Health System Context: {form_data['health_system_info']}" if form_data.get('health_system_info') else ""}

Generate 5-7 specific talking points this candidate should weave into their interview answers. Each point should:
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
            logger.warning("Could not parse AI talking points, using fallback.")

    # Fallback if AI fails
    return [
        f"Highlight your experience with the specific Epic modules or technical skills mentioned in the job description for {form_data['job_title']}.",
        f"Demonstrate your understanding of {form_data['health_system_name']}'s environment and how your skills align with their needs.",
        "Share examples of successful go-lives, optimizations, or implementations you've led.",
        "Emphasize your ability to work collaboratively with clinical end-users and translate technical concepts for non-technical stakeholders.",
        "Discuss your approach to troubleshooting and problem-solving under pressure during critical system events.",
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

Generate 5-6 thoughtful questions the candidate should ask the interviewer. These should:
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
            logger.warning("Could not parse AI questions, using fallback.")

    return [
        "What does a typical day look like in this role?",
        "What are the biggest challenges the team is currently facing?",
        "How does the team handle knowledge transfer and documentation?",
        f"What are {form_data['health_system_name']}'s top IT priorities for the next 12 months?",
        "How do you measure success for someone in this position?",
        "What's the team culture like — how do people collaborate day-to-day?",
    ]


def _generate_interviewer_insights(form_data: dict) -> str:
    """AI-generated insights about the interviewer based on provided info."""
    if not form_data.get("interviewer_name"):
        return ""

    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

The candidate will be interviewing with:
Name: {form_data['interviewer_name']}
Title: {form_data.get('interviewer_title', 'Not provided')}
LinkedIn: {form_data.get('interviewer_linkedin', 'Not provided')}
Background notes: {form_data.get('interviewer_background', 'Not provided')}

Health System: {form_data['health_system_name']}
Role being interviewed for: {form_data['job_title']}

Write a brief 2-3 paragraph summary that helps the candidate understand:
1. What this interviewer likely cares about based on their role/title
2. How to connect with them (common ground, topics to emphasize)
3. What kind of questions they're likely to ask given their position

Keep it practical and actionable. No fluff. Do NOT invent biographical details — only work with what's provided. If little info is given, focus on what their title tells us about their perspective."""

    result = _call_claude(prompt)
    return result if result else ""


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
   - "point":    a short (≤10 word) headline naming the strength (e.g., "Epic Ambulatory go-live leadership")
   - "evidence": a 1–2 sentence specific example from their background that proves it, phrased in second person ("You led the go-live at...")

2. "gaps_to_address": an array of 2–4 objects, each with:
   - "gap":     a short (≤10 word) headline naming an area where the candidate is lighter than the JD asks for
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


def _generate_likely_questions(form_data: dict) -> list[str]:
    """AI-generated questions the interviewer is likely to ask, so the candidate can prepare."""
    prompt = f"""You are helping a healthcare IT consultant prepare for a job interview.

Role: {form_data['job_title']}
Health System: {form_data['health_system_name']}
Job Description:
{form_data['job_description']}

{f"Interviewer: {form_data['interviewer_name']}, {form_data['interviewer_title']}" if form_data.get('interviewer_name') else ""}
{f"Interviewer Background: {form_data['interviewer_background']}" if form_data.get('interviewer_background') else ""}

Generate 6-8 questions the interviewer is likely to ask the candidate based on the job description and role. Include a mix of:
- Technical/skill-based questions specific to the role
- Behavioral questions (e.g. "Tell me about a time when...")
- Situational questions related to healthcare IT

For each question, add a brief one-sentence tip in parentheses on how to approach the answer.

Return ONLY a JSON array of strings. No markdown, no explanation. Example:
["Question here? (Tip: Focus on specific outcomes and metrics.)"]"""

    result = _call_claude(prompt)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Could not parse AI likely questions, using fallback.")

    return [
        f"Tell me about your experience with the technologies mentioned in the {form_data['job_title']} job description. (Tip: Be specific — name the modules, tools, or systems you've worked with.)",
        "Describe a challenging go-live or system implementation you supported. What was your role and how did you handle obstacles? (Tip: Use the STAR method — Situation, Task, Action, Result.)",
        "How do you prioritize tasks when you have multiple urgent requests from different departments? (Tip: Give a real example showing your decision-making process.)",
        f"Why are you interested in working at {form_data['health_system_name']}? (Tip: Reference something specific about the organization — their mission, recent initiatives, or growth.)",
        "How do you handle pushback from clinical end-users during a system change or workflow update? (Tip: Show empathy for the user's perspective while explaining how you drive adoption.)",
        "Where do you see yourself in 2-3 years? (Tip: Align your growth goals with the opportunities this role provides.)",
    ]


# ─── MAIN GENERATOR ─────────────────────────────────────────────────────

def generate_interview_guide(form_data: dict, fit_text: str = "") -> dict:
    """
    Generate the full interview guide content.
    Returns a dict with all sections ready for PDF rendering.

    fit_text: optional text of the recruiter's candidate fit analysis. If provided,
              a structured "Why You're a Fit" section is generated.
    """
    talking_points = _generate_talking_points(form_data)
    questions_to_ask = _generate_questions_to_ask(form_data)
    likely_questions = _generate_likely_questions(form_data)
    interviewer_insights = _generate_interviewer_insights(form_data)
    fit_analysis = _generate_fit_analysis(form_data, fit_text)

    # Use custom interview tips from form if provided, otherwise defaults
    custom_tips_text = form_data.get("interview_tips", "").strip()
    if custom_tips_text:
        interview_tips = [
            line.strip() for line in custom_tips_text.splitlines()
            if line.strip()
        ]
    else:
        interview_tips = list(DEFAULT_INTERVIEW_TIPS)

    return {
        "talking_points": talking_points,
        "questions_to_ask": questions_to_ask,
        "likely_questions": likely_questions,
        "interviewer_insights": interviewer_insights,
        "fit_analysis": fit_analysis,
        "general_tips": GENERAL_TIPS,
        "interview_tips": interview_tips,
        "follow_up_tips": FOLLOW_UP_TIPS,
        "day_of_checklist": DAY_OF_CHECKLIST,
    }
