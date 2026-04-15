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

GENERAL_TIPS = [
    "Research the organization thoroughly before the interview — review their website, recent news, mission statement, and any publicly available strategic plans.",
    "Arrive 10–15 minutes early. If virtual, test your audio/video setup 30 minutes beforehand and have a backup plan (phone dial-in number) ready.",
    "Dress professionally — business formal unless told otherwise. When in doubt, overdress rather than underdress.",
    "Bring multiple copies of your resume, a notepad, and a pen. Have a list of your references ready in case they ask.",
    "Prepare 2–3 concise stories using the STAR method (Situation, Task, Action, Result) that demonstrate your relevant experience.",
    "Make eye contact, offer a firm handshake, and address each interviewer by name.",
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
    "Confirm the interview time, location, and format (in-person, phone, or video).",
    "If in-person: look up the address, parking situation, and building entrance ahead of time.",
    "If virtual: test your internet, camera, and microphone. Close unnecessary browser tabs and apps.",
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


# ─── MAIN GENERATOR ─────────────────────────────────────────────────────

def generate_interview_guide(form_data: dict) -> dict:
    """
    Generate the full interview guide content.
    Returns a dict with all sections ready for PDF rendering.
    """
    talking_points = _generate_talking_points(form_data)
    questions_to_ask = _generate_questions_to_ask(form_data)
    interviewer_insights = _generate_interviewer_insights(form_data)

    return {
        "talking_points": talking_points,
        "questions_to_ask": questions_to_ask,
        "interviewer_insights": interviewer_insights,
        "general_tips": GENERAL_TIPS,
        "follow_up_tips": FOLLOW_UP_TIPS,
        "day_of_checklist": DAY_OF_CHECKLIST,
    }
