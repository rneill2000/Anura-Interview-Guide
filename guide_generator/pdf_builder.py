"""
PDF builder for Interview Guides — Anura Connect branding.

Uses WeasyPrint (HTML → PDF) for polished, magazine-style output
matching the Exact Sciences sample guide design.
"""

from pathlib import Path
import html as html_module

# ─── ANURA CONNECT BRAND COLORS (matches Resume Tool palette) ────────────
NAVY = "#071a2c"          # anura-950
NAVY_DARK = "#0a2239"     # anura-900
TEAL = "#1a6b8a"          # anura-500 (primary)
TEAL_DARK = "#145a75"     # anura-600
LIGHT_BLUE = "#e8f4f8"    # anura-50
LIGHT_BLUE_2 = "#c8e4ed"  # anura-100
ACCENT = "#3d8a9e"        # accent-500
DARK_GRAY = "#1f2937"
MED_GRAY = "#6b7280"
LIGHT_GRAY = "#f9fafb"


def _esc(text: str) -> str:
    """HTML-escape user input."""
    return html_module.escape(str(text)) if text else ""


def _build_cover_page(form_data: dict) -> str:
    """Cover page with hero background and title overlay."""
    from guide_generator.logo_data import LOGO_BASE64

    title = f"Interview Preparation Guide: {_esc(form_data['job_title'])} at {_esc(form_data['health_system_name'])}"

    return f"""
    <div class="cover-page">
        <div class="cover-overlay">
            <div class="cover-content">
                <img src="{LOGO_BASE64}" alt="Anura Connect" class="cover-logo" />
                <h1 class="cover-title">{title}</h1>
                <p class="cover-subtitle">Prepared for {_esc(form_data['candidate_name'])}</p>
                {f'<p class="cover-date">{_esc(form_data.get("interview_date", ""))}</p>' if form_data.get('interview_date') else ''}
            </div>
        </div>
    </div>
    """


def _build_role_section(form_data: dict) -> str:
    """The Role section with job description."""
    jd = _esc(form_data['job_description']).replace('\n', '<br>')

    return f"""
    <div class="section">
        <h2 class="section-title">The Role</h2>
        <h3 class="role-title">{_esc(form_data['job_title'])}</h3>
        <div class="role-description">{jd}</div>
    </div>
    """


def _build_health_system_section(form_data: dict) -> str:
    """About the health system."""
    if not form_data.get('health_system_info'):
        return ""

    info = _esc(form_data['health_system_info']).replace('\n', '<br>')

    return f"""
    <div class="section">
        <h2 class="section-title">About {_esc(form_data['health_system_name'])}</h2>
        <div class="body-text">{info}</div>
    </div>
    """


def _build_interviewer_section(form_data: dict, guide_content: dict) -> str:
    """Your Interviewer section matching the Exact Sciences sample."""
    if not form_data.get('interviewer_name'):
        return ""

    name = _esc(form_data['interviewer_name'])
    title = _esc(form_data.get('interviewer_title', ''))
    linkedin = form_data.get('interviewer_linkedin', '')
    insights = guide_content.get('interviewer_insights', '')

    name_html = f'<a href="{_esc(linkedin)}" class="interviewer-link">{name}</a>' if linkedin else f'<span class="interviewer-name-text">{name}</span>'

    title_html = f'<p class="interviewer-role">Role: {title} at {_esc(form_data["health_system_name"])}</p>' if title else ''

    insights_html = ""
    if insights:
        paragraphs = insights.strip().split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if p:
                insights_html += f'<p class="body-text">{_esc(p)}</p>'

    return f"""
    <div class="section interviewer-section">
        <h2 class="section-title">Your Interviewer</h2>
        <div class="interviewer-name">{name_html}</div>
        {title_html}
        {insights_html}
    </div>
    """


def _build_essentials_cards(form_data: dict) -> str:
    """Pre-Interview Essentials as 2x2 card grid (matches Exact Sciences sample)."""

    interview_format = form_data.get('interview_format', 'In-Person')
    is_virtual = 'video' in interview_format.lower() or 'zoom' in interview_format.lower() or 'teams' in interview_format.lower() or 'phone' in interview_format.lower()

    tech_text = ("Test your video/audio 30 minutes before the call. Ensure stable internet connection, "
                 "working camera, and clear microphone. Have the meeting link ready and join 2–3 minutes early."
                 if is_virtual else
                 "Arrive 10–15 minutes early. Know the building entrance, parking, and check-in process. "
                 "Bring a charged phone as backup for any last-minute coordination.")

    # SVG icons for the cards (renders cleanly in WeasyPrint)
    icon_monitor = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
    icon_chart = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
    icon_shirt = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M16 2l4 4-3 1v13H7V7L4 6l4-4 4 3 4-3z"/></svg>'
    icon_doc = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'

    cards = [
        ("Technology Check" if is_virtual else "Arrival Plan",
         icon_monitor,
         tech_text),
        ("Company Research",
         icon_chart,
         f"Review {_esc(form_data['health_system_name'])}'s website, recent news, and organizational structure. "
         "Prepare a couple of questions related to the organization as a whole."),
        ("Professional Appearance",
         icon_shirt,
         "Dress in business professional attire." +
         (" Ensure your background is clean and professional or use a filter." if is_virtual else "") +
         " First impressions matter — when in doubt, overdress."),
        ("Materials Ready",
         icon_doc,
         "Have your resume and specific examples of relevant projects accessible. "
         "Prepare questions about the team, current challenges, where they excel, and where they're headed in the next 6 to 12 months."),
    ]

    cards_html = ""
    for title, icon, text in cards:
        cards_html += f"""
        <div class="essential-card">
            <div class="card-icon">{icon}</div>
            <h4 class="card-title">{title}</h4>
            <p class="card-text">{text}</p>
        </div>
        """

    return f"""
    <div class="section">
        <h2 class="section-title">Pre-Interview Essentials</h2>
        <div class="card-grid">{cards_html}</div>
    </div>
    """


def _build_talking_points(guide_content: dict) -> str:
    """Key talking points section."""
    points = guide_content.get('talking_points', [])
    if not points:
        return ""

    items = ""
    for i, point in enumerate(points, 1):
        items += f"""
        <div class="talking-point">
            <div class="point-number">{i}</div>
            <div class="point-text">{_esc(point)}</div>
        </div>
        """

    return f"""
    <div class="section">
        <h2 class="section-title">Key Talking Points</h2>
        <p class="section-subtitle">Weave these into your interview answers to demonstrate alignment with the role.</p>
        {items}
    </div>
    """


def _build_questions_to_ask(guide_content: dict) -> str:
    """Questions the candidate should ask."""
    questions = guide_content.get('questions_to_ask', [])
    if not questions:
        return ""

    items = ""
    for q in questions:
        items += f'<div class="question-item">&#8220;{_esc(q)}&#8221;</div>'

    return f"""
    <div class="section">
        <h2 class="section-title">Questions to Ask</h2>
        <p class="section-subtitle">Asking thoughtful questions shows preparation and genuine interest.</p>
        <div class="questions-list">{items}</div>
    </div>
    """


def _build_best_practices(guide_content: dict) -> str:
    """General interview tips in a clean two-column layout."""
    tips = guide_content.get('general_tips', [])
    if not tips:
        return ""

    mid = (len(tips) + 1) // 2
    col1 = "".join(f'<li>{_esc(t)}</li>' for t in tips[:mid])
    col2 = "".join(f'<li>{_esc(t)}</li>' for t in tips[mid:])

    return f"""
    <div class="section">
        <h2 class="section-title">Interview Best Practices</h2>
        <div class="two-col">
            <ul class="tips-list">{col1}</ul>
            <ul class="tips-list">{col2}</ul>
        </div>
    </div>
    """


def _build_follow_up(guide_content: dict) -> str:
    """Follow-up guidance section."""
    tips = guide_content.get('follow_up_tips', [])
    if not tips:
        return ""

    items = "".join(f'<li>{_esc(t)}</li>' for t in tips)

    return f"""
    <div class="section">
        <h2 class="section-title">After the Interview</h2>
        <ul class="tips-list">{items}</ul>
    </div>
    """


def _build_contact_footer(form_data: dict) -> str:
    """Anura Connect contact box."""
    parts = []
    if form_data.get('contact_name'):
        parts.append(f"<strong>{_esc(form_data['contact_name'])}</strong>")
    if form_data.get('contact_email'):
        parts.append(_esc(form_data['contact_email']))
    if form_data.get('contact_phone'):
        parts.append(_esc(form_data['contact_phone']))

    if not parts:
        return ""

    return f"""
    <div class="contact-footer">
        <div class="contact-inner">
            <h3 class="contact-title">Your Anura Connect Contact</h3>
            <p class="contact-info">{" &nbsp;|&nbsp; ".join(parts)}</p>
            <p class="contact-cta">Reach out with any questions before your interview — we're here to help you succeed.</p>
        </div>
    </div>
    """


def _get_css() -> str:
    """Full CSS for the PDF — magazine-style layout matching Exact Sciences sample."""
    return f"""
    @page {{
        size: letter;
        margin: 0;
    }}

    @page content {{
        margin: 48pt 48pt 60pt 48pt;
    }}

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: {DARK_GRAY};
        font-size: 10.5pt;
        line-height: 1.6;
    }}

    /* ─── COVER PAGE ─── */
    .cover-page {{
        page: initial;
        width: 8.5in;
        height: 11in;
        position: relative;
        background: linear-gradient(135deg, {NAVY} 0%, {NAVY_DARK} 60%, {TEAL_DARK} 100%);
        page-break-after: always;
    }}

    .cover-overlay {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 60pt;
    }}

    .cover-content {{
        text-align: left;
        max-width: 6in;
    }}

    .cover-logo {{
        width: 50pt;
        height: 50pt;
        margin-bottom: 30pt;
    }}

    .cover-title {{
        font-size: 28pt;
        font-weight: 700;
        color: white;
        line-height: 1.2;
        margin-bottom: 16pt;
        letter-spacing: -0.5pt;
    }}

    .cover-subtitle {{
        font-size: 14pt;
        color: {LIGHT_BLUE_2};
        font-weight: 400;
        margin-bottom: 8pt;
    }}

    .cover-date {{
        font-size: 11pt;
        color: {ACCENT};
        font-weight: 500;
    }}

    /* ─── CONTENT PAGES ─── */
    .section {{
        page: content;
        margin-bottom: 28pt;
    }}

    .section-title {{
        font-size: 22pt;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 6pt;
        letter-spacing: -0.3pt;
    }}

    .section-subtitle {{
        font-size: 10pt;
        color: {MED_GRAY};
        margin-bottom: 16pt;
    }}

    .role-title {{
        font-size: 14pt;
        font-weight: 700;
        color: {DARK_GRAY};
        margin-bottom: 12pt;
    }}

    .role-description {{
        font-size: 10pt;
        line-height: 1.65;
        color: {DARK_GRAY};
    }}

    .body-text {{
        font-size: 10.5pt;
        line-height: 1.65;
        color: {DARK_GRAY};
        margin-bottom: 10pt;
    }}

    /* ─── INTERVIEWER ─── */
    .interviewer-section {{
        page-break-before: auto;
    }}

    .interviewer-name {{
        margin-bottom: 4pt;
    }}

    .interviewer-link {{
        font-size: 16pt;
        font-weight: 700;
        color: {TEAL};
        text-decoration: underline;
    }}

    .interviewer-name-text {{
        font-size: 16pt;
        font-weight: 700;
        color: {NAVY};
    }}

    .interviewer-role {{
        font-size: 11pt;
        font-weight: 600;
        color: {DARK_GRAY};
        margin-bottom: 14pt;
    }}

    /* ─── PRE-INTERVIEW ESSENTIALS CARDS ─── */
    .card-grid {{
        display: flex;
        flex-wrap: wrap;
        gap: 12pt;
        margin-top: 12pt;
    }}

    .essential-card {{
        background: {LIGHT_BLUE};
        border-radius: 8pt;
        padding: 20pt;
        width: 48%;
        border: 1pt solid {LIGHT_BLUE_2};
    }}

    .card-icon {{
        width: 36pt;
        height: 36pt;
        background: {NAVY};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16pt;
        margin-bottom: 10pt;
        color: white;
        text-align: center;
        line-height: 36pt;
    }}

    .card-title {{
        font-size: 12pt;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 6pt;
    }}

    .card-text {{
        font-size: 9.5pt;
        line-height: 1.55;
        color: {DARK_GRAY};
    }}

    /* ─── TALKING POINTS ─── */
    .talking-point {{
        display: flex;
        align-items: flex-start;
        gap: 12pt;
        margin-bottom: 12pt;
        padding: 12pt 14pt;
        background: {LIGHT_GRAY};
        border-radius: 6pt;
        border-left: 3pt solid {TEAL};
    }}

    .point-number {{
        width: 24pt;
        height: 24pt;
        min-width: 24pt;
        background: {TEAL};
        color: white;
        border-radius: 50%;
        font-size: 10pt;
        font-weight: 700;
        text-align: center;
        line-height: 24pt;
    }}

    .point-text {{
        font-size: 10pt;
        line-height: 1.55;
        color: {DARK_GRAY};
    }}

    /* ─── QUESTIONS TO ASK ─── */
    .questions-list {{
        margin-top: 8pt;
    }}

    .question-item {{
        font-size: 10.5pt;
        color: {DARK_GRAY};
        padding: 10pt 14pt;
        border-bottom: 1pt solid #e5e7eb;
        font-style: italic;
    }}

    .question-item:last-child {{
        border-bottom: none;
    }}

    /* ─── TWO-COLUMN TIPS ─── */
    .two-col {{
        display: flex;
        gap: 24pt;
    }}

    .two-col .tips-list {{
        flex: 1;
    }}

    .tips-list {{
        padding-left: 16pt;
    }}

    .tips-list li {{
        font-size: 10pt;
        line-height: 1.55;
        color: {DARK_GRAY};
        margin-bottom: 8pt;
    }}

    /* ─── CONTACT FOOTER ─── */
    .contact-footer {{
        margin-top: 24pt;
        page-break-inside: avoid;
    }}

    .contact-inner {{
        background: {LIGHT_BLUE};
        border: 1pt solid {LIGHT_BLUE_2};
        border-radius: 8pt;
        padding: 20pt 24pt;
        text-align: center;
    }}

    .contact-title {{
        font-size: 13pt;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 6pt;
    }}

    .contact-info {{
        font-size: 10.5pt;
        color: {DARK_GRAY};
        margin-bottom: 6pt;
    }}

    .contact-cta {{
        font-size: 9pt;
        color: {MED_GRAY};
        font-style: italic;
    }}

    /* ─── PAGE FOOTER ─── */
    .page-footer {{
        text-align: center;
        font-size: 8pt;
        color: {MED_GRAY};
        margin-top: 30pt;
        padding-top: 12pt;
        border-top: 0.5pt solid #e5e7eb;
    }}
    """


def build_guide_pdf(guide_content: dict, form_data: dict, output_path: Path):
    """Build the full interview guide PDF using WeasyPrint."""
    from weasyprint import HTML

    sections = [
        _build_cover_page(form_data),
        _build_role_section(form_data),
        _build_health_system_section(form_data),
        _build_interviewer_section(form_data, guide_content),
        _build_essentials_cards(form_data),
        _build_talking_points(guide_content),
        _build_questions_to_ask(guide_content),
        _build_best_practices(guide_content),
        _build_follow_up(guide_content),
        _build_contact_footer(form_data),
    ]

    body = "\n".join(s for s in sections if s)

    html_str = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>{_get_css()}</style>
</head>
<body>
    {body}
    <div class="page-footer">
        Prepared by Anura Connect &nbsp;|&nbsp; anuraconnect.com &nbsp;|&nbsp; Confidential
    </div>
</body>
</html>"""

    HTML(string=html_str).write_pdf(str(output_path))
