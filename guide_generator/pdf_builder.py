"""PDF builder for Interview Guides — Anura Connect branding.

Uses ReportLab for polished, modern output.
Cover page + clean interior with consistent card-based design.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem, PageBreak, Image,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
import io
import base64


# ─── ANURA CONNECT BRAND COLORS ────────────────────────────────────────

NAVY = HexColor("#071a2c")
NAVY_MID = HexColor("#0a2239")
TEAL = HexColor("#1a6b8a")
TEAL_DARK = HexColor("#145a75")
TEAL_LIGHT = HexColor("#2a8baa")
LIGHT_BLUE = HexColor("#e8f4f8")
LIGHT_BLUE_2 = HexColor("#c8e4ed")
ACCENT = HexColor("#3d8a9e")
DARK_GRAY = HexColor("#1f2937")
MED_GRAY = HexColor("#6b7280")
LIGHT_GRAY = HexColor("#f8f9fa")
CARD_BG = HexColor("#f1f7fa")
WHITE = HexColor("#FFFFFF")
BORDER_GRAY = HexColor("#e5e7eb")
BORDER_LIGHT = HexColor("#d1d5db")

PAGE_W, PAGE_H = letter
MARGIN = 58


def _styles():
    """Build all paragraph styles."""
    s = {}

    s['cover_title'] = ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=26,
        leading=32, textColor=WHITE, spaceAfter=12,
    )
    s['cover_sub'] = ParagraphStyle(
        'CoverSub', fontName='Helvetica', fontSize=13,
        textColor=LIGHT_BLUE_2, spaceAfter=6,
    )
    s['cover_date'] = ParagraphStyle(
        'CoverDate', fontName='Helvetica', fontSize=11,
        textColor=ACCENT,
    )
    s['section_title'] = ParagraphStyle(
        'SectionTitle', fontName='Helvetica-Bold', fontSize=20,
        leading=26, textColor=NAVY, spaceBefore=10, spaceAfter=6,
    )
    s['section_subtitle'] = ParagraphStyle(
        'SectionSubtitle', fontName='Helvetica', fontSize=10,
        textColor=MED_GRAY, spaceAfter=14, leading=14.5,
    )
    s['role_title'] = ParagraphStyle(
        'RoleTitle', fontName='Helvetica-Bold', fontSize=14,
        textColor=TEAL, spaceAfter=10,
    )
    s['body'] = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=10.5,
        leading=16, textColor=DARK_GRAY, spaceAfter=10,
    )
    s['body_small'] = ParagraphStyle(
        'BodySmall', fontName='Helvetica', fontSize=9.5,
        leading=14, textColor=DARK_GRAY, spaceAfter=5,
    )
    s['interviewer_name'] = ParagraphStyle(
        'InterviewerName', fontName='Helvetica-Bold', fontSize=16,
        textColor=TEAL, spaceAfter=4,
    )
    s['interviewer_role'] = ParagraphStyle(
        'InterviewerRole', fontName='Helvetica-Bold', fontSize=10,
        textColor=DARK_GRAY, spaceAfter=12,
    )
    s['card_title'] = ParagraphStyle(
        'CardTitle', fontName='Helvetica-Bold', fontSize=11.5,
        textColor=NAVY, spaceAfter=6,
    )
    s['card_text'] = ParagraphStyle(
        'CardText', fontName='Helvetica', fontSize=9.5,
        leading=14, textColor=DARK_GRAY,
    )
    s['point_text'] = ParagraphStyle(
        'PointText', fontName='Helvetica', fontSize=10.5,
        leading=15.5, textColor=DARK_GRAY,
    )
    s['question'] = ParagraphStyle(
        'Question', fontName='Helvetica-Oblique', fontSize=10.5,
        leading=15.5, textColor=DARK_GRAY, leftIndent=12,
    )
    s['tip'] = ParagraphStyle(
        'Tip', fontName='Helvetica', fontSize=10,
        leading=15, textColor=DARK_GRAY, bulletIndent=0, leftIndent=14,
    )
    s['contact_title'] = ParagraphStyle(
        'ContactTitle', fontName='Helvetica-Bold', fontSize=14,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=6,
    )
    s['contact_info'] = ParagraphStyle(
        'ContactInfo', fontName='Helvetica', fontSize=11,
        textColor=DARK_GRAY, alignment=TA_CENTER, spaceAfter=5,
    )
    s['contact_cta'] = ParagraphStyle(
        'ContactCta', fontName='Helvetica-Oblique', fontSize=9,
        textColor=MED_GRAY, alignment=TA_CENTER,
    )
    s['footer'] = ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=8,
        textColor=MED_GRAY, alignment=TA_CENTER,
    )
    return s


def _draw_cover(canvas, doc, form_data):
    """Draw the full-bleed cover page."""
    canvas.saveState()

    # Gradient background (navy to teal)
    steps = 60
    for i in range(steps):
        frac = i / steps
        r = 7/255 * (1 - frac * 0.3) + 26/255 * frac * 0.3
        g = 26/255 * (1 - frac * 0.5) + 107/255 * frac * 0.5
        b = 44/255 * (1 - frac * 0.4) + 138/255 * frac * 0.4
        canvas.setFillColor(Color(r, g, b))
        y = PAGE_H - (PAGE_H * (i + 1) / steps)
        canvas.rect(0, y, PAGE_W, PAGE_H / steps + 1, fill=1, stroke=0)

    # Logo
    try:
        from guide_generator.logo_data import LOGO_BASE64
        logo_b64 = LOGO_BASE64.split(",", 1)[1]
        logo_bytes = base64.b64decode(logo_b64)
        logo_img = ImageReader(io.BytesIO(logo_bytes))
        canvas.drawImage(logo_img, 72, PAGE_H - 220, width=80, height=80,
                         preserveAspectRatio=True, mask='auto')
    except Exception:
        # Fallback: draw a teal rounded rect with "A"
        canvas.setFillColor(TEAL)
        canvas.roundRect(72, PAGE_H - 220, 50, 50, 8, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 26)
        canvas.drawCentredString(97, PAGE_H - 208, "A")

    # Title
    title = f"Interview Preparation Guide: {form_data['job_title']} at {form_data['health_system_name']}"
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 26)

    # Word-wrap the title
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if canvas.stringWidth(test, "Helvetica-Bold", 26) > PAGE_W - 160:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    y = PAGE_H - 280
    for line in lines:
        canvas.drawString(72, y, line)
        y -= 36

    # Subtitle
    y -= 16
    canvas.setFillColor(LIGHT_BLUE_2)
    canvas.setFont("Helvetica", 13)
    canvas.drawString(72, y, f"Prepared for {form_data['candidate_name']}")

    # Date
    if form_data.get('interview_date'):
        y -= 22
        canvas.setFillColor(ACCENT)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(72, y, form_data['interview_date'])

    canvas.restoreState()


def _section_divider(story, title, styles):
    """Add a section title with teal accent line."""
    story.append(Spacer(1, 20))
    story.append(Paragraph(title, styles['section_title']))
    story.append(HRFlowable(width="100%", thickness=2.5, color=TEAL,
                             spaceAfter=8, spaceBefore=2))


def _build_card(title, text, styles, width):
    """Build a single essentials card as a Table with modern styling."""
    # Icon circle
    d = Drawing(28, 28)
    d.add(Circle(14, 14, 14, fillColor=NAVY, strokeColor=None))
    d.add(String(14, 8.5, "+", fontSize=14, fillColor=WHITE,
                 textAnchor='middle', fontName='Helvetica-Bold'))

    content = [
        [d],
        [Spacer(1, 4)],
        [Paragraph(f"<b>{title}</b>", styles['card_title'])],
        [Paragraph(text, styles['card_text'])],
    ]
    card = Table(content, colWidths=[width])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, LIGHT_BLUE_2),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('TOPPADDING', (0, 0), (0, 0), 16),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 16),
    ]))
    return card


def _build_talking_point(number, text, styles, width):
    """Build a numbered talking point row with modern styling."""
    # Number circle
    d = Drawing(24, 24)
    d.add(Circle(12, 12, 12, fillColor=TEAL, strokeColor=None))
    d.add(String(12, 6, str(number), fontSize=10, fillColor=WHITE,
                 textAnchor='middle', fontName='Helvetica-Bold'))

    row = Table(
        [[d, Paragraph(text, styles['point_text'])]],
        colWidths=[36, width - 36],
    )
    row.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 6),
        ('RIGHTPADDING', (-1, -1), (-1, -1), 14),
    ]))

    # Outer wrapper with left teal accent border
    outer = Table([[row]], colWidths=[width])
    outer.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LINEBEFORE', (0, 0), (0, -1), 3, TEAL),
    ]))
    return outer


def _build_question_row(text, styles, width):
    """Build a question row with subtle background and left accent."""
    row = Table(
        [[Paragraph(f"\u201c{text}\u201d", styles['question'])]],
        colWidths=[width],
    )
    row.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('LINEBEFORE', (0, 0), (0, -1), 2.5, ACCENT),
    ]))
    return row


def _build_tip_item(text, styles, width):
    """Build an individual tip as a clean row with checkmark."""
    check_style = ParagraphStyle(
        'TipCheck', parent=styles['body_small'],
        textColor=TEAL, fontName='Helvetica-Bold', fontSize=10,
    )
    row = Table(
        [[Paragraph("\u2713", check_style), Paragraph(text, styles['tip'])]],
        colWidths=[22, width - 22],
    )
    row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return row


def build_guide_pdf(guide_content: dict, form_data: dict, output_path: Path):
    """Build the full interview guide PDF."""

    content_width = PAGE_W - 2 * MARGIN
    styles = _styles()

    # We'll collect the form_data for the cover page callback
    cover_data = dict(form_data)

    def on_first_page(canvas, doc):
        _draw_cover(canvas, doc, cover_data)

    def on_later_pages(canvas, doc):
        # Subtle teal top bar on content pages
        canvas.saveState()
        canvas.setFillColor(TEAL)
        canvas.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)
        # Footer
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MED_GRAY)
        canvas.drawCentredString(PAGE_W / 2, 24,
            "Prepared by Anura Connect  \u2502  anuraconnect.com  \u2502  Confidential")
        # Thin footer line
        canvas.setStrokeColor(BORDER_GRAY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, 38, PAGE_W - MARGIN, 38)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN + 8,
        bottomMargin=MARGIN + 12,
    )

    story = []

    # ── Cover page (drawn via canvas callback, just force a page break) ──
    story.append(PageBreak())

    # ── The Role ──
    _section_divider(story, "The Role", styles)
    story.append(Paragraph(form_data['job_title'], styles['role_title']))
    jd = form_data['job_description'].replace('\n', '<br/>')
    story.append(Paragraph(jd, styles['body']))

    # ── About the Client ──
    _section_divider(story, f"About {form_data['health_system_name']}", styles)
    if form_data.get('health_system_info'):
        info = form_data['health_system_info'].replace('\n', '<br/>')
        story.append(Paragraph(info, styles['body']))
    else:
        story.append(Paragraph(
            f"Visit {form_data['health_system_name']}\u2019s website to learn about their mission, values, and recent initiatives before your interview.",
            styles['body'],
        ))

    # ── Recent News ──
    if guide_content.get('recent_news'):
        _section_divider(story, f"Recent News: {form_data['health_system_name']}", styles)
        story.append(Paragraph(
            "Stay current — referencing recent events shows you've done your homework.",
            styles['section_subtitle'],
        ))
        for item in guide_content['recent_news']:
            headline = item.get('headline', '')
            summary = item.get('summary', '')
            date = item.get('date', '')
            relevance = item.get('relevance', '')

            news_rows = []
            date_str = f'<font color="#6b7280" size="8">  {date}</font>' if date else ''
            news_rows.append([Paragraph(
                f'<b>{headline}</b>{date_str}', styles['card_title']
            )])

            if summary:
                news_rows.append([Paragraph(summary, styles['body_small'])])

            if relevance:
                relevance_style = ParagraphStyle(
                    'NewsRelevance', parent=styles['body_small'],
                    fontName='Helvetica-Oblique', textColor=TEAL, fontSize=8.5,
                )
                news_rows.append([Paragraph(f"Why it matters: {relevance}", relevance_style)])

            news_card = Table(news_rows, colWidths=[content_width - 8])
            news_card.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
                ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ('TOPPADDING', (0, 0), (0, 0), 10),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
                ('LINEBEFORE', (0, 0), (0, -1), 3, TEAL),
            ]))
            story.append(news_card)
            story.append(Spacer(1, 6))

    # ── Your Interviewer ──
    if form_data.get('interviewer_name'):
        _section_divider(story, "Your Interviewer", styles)
        name = form_data['interviewer_name']
        if form_data.get('interviewer_linkedin'):
            name = f'<a href="{form_data["interviewer_linkedin"]}" color="#1a6b8a"><u>{name}</u></a>'
        story.append(Paragraph(name, styles['interviewer_name']))
        if form_data.get('interviewer_title'):
            story.append(Paragraph(
                f"Role: {form_data['interviewer_title']} at {form_data['health_system_name']}",
                styles['interviewer_role'],
            ))
        if guide_content.get('interviewer_insights'):
            for para in guide_content['interviewer_insights'].strip().split('\n\n'):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, styles['body']))

    # ── Pre-Interview Essentials (2x2 card grid) ──
    _section_divider(story, "Before the Interview", styles)
    story.append(Paragraph(
        "Complete these steps before your interview to set yourself up for success.",
        styles['section_subtitle'],
    ))

    is_virtual = any(k in form_data.get('interview_format', '').lower()
                     for k in ('video', 'zoom', 'teams', 'phone'))

    tech_text = ("Test your video/audio 30 minutes before the call. Ensure stable internet, "
                 "working camera, and clear microphone. Have the meeting link ready."
                 if is_virtual else
                 "Arrive 10\u201315 minutes early. Know the building entrance, parking, and check-in process.")

    card_w = (content_width - 14) / 2
    cards = [
        ("Technology Check" if is_virtual else "Arrival Plan", tech_text),
        ("Company Research",
         f"Review {form_data['health_system_name']}\u2019s website, recent news, and structure. "
         "Prepare questions about the organization."),
        ("Professional Appearance",
         "Dress in business professional attire." +
         (" Ensure your background is clean and professional." if is_virtual else "") +
         " First impressions matter \u2014 when in doubt, overdress."),
        ("Materials Ready",
         "Have your resume and specific project examples accessible. "
         "Prepare questions about the team, challenges, and 6\u201312 month direction."),
    ]

    c = [_build_card(t, txt, styles, card_w) for t, txt in cards]
    grid = Table(
        [[c[0], c[1]], [c[2], c[3]]],
        colWidths=[card_w + 7, card_w + 7],
        rowHeights=None,
    )
    grid.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(grid)

    # ── Key Talking Points ──
    if guide_content.get('talking_points'):
        _section_divider(story, "Key Talking Points", styles)
        story.append(Paragraph(
            "Weave these into your interview answers to demonstrate alignment with the role.",
            styles['section_subtitle'],
        ))
        for i, point in enumerate(guide_content['talking_points'], 1):
            story.append(_build_talking_point(i, point, styles, content_width))
            story.append(Spacer(1, 5))

    # ── Questions to Ask ──
    if guide_content.get('questions_to_ask'):
        _section_divider(story, "Questions to Ask", styles)
        story.append(Paragraph(
            "Asking thoughtful questions shows preparation and genuine interest.",
            styles['section_subtitle'],
        ))
        for q in guide_content['questions_to_ask']:
            story.append(_build_question_row(q, styles, content_width))
            story.append(Spacer(1, 5))

    # ── Prepare For These Questions (AI-generated likely interview questions) ──
    if guide_content.get('likely_questions'):
        _section_divider(story, "Prepare For These Questions", styles)
        story.append(Paragraph(
            "Based on the role and job description, you may be asked questions like these. "
            "Think through your answers ahead of time.",
            styles['section_subtitle'],
        ))
        for i, q in enumerate(guide_content['likely_questions'], 1):
            story.append(_build_talking_point(i, q, styles, content_width))
            story.append(Spacer(1, 5))



    # ── After the Interview (compact) ──
    if guide_content.get('follow_up_tips'):
        _section_divider(story, "After the Interview", styles)
        tips = guide_content['follow_up_tips'][:4]
        for tip in tips:
            story.append(_build_tip_item(tip, styles, content_width))

    # ── Contact Footer ──
    if any(form_data.get(k) for k in ('contact_name', 'contact_email', 'contact_phone')):
        story.append(Spacer(1, 24))
        parts = []
        if form_data.get('contact_name'):
            parts.append(f"<b>{form_data['contact_name']}</b>")
        if form_data.get('contact_email'):
            parts.append(form_data['contact_email'])
        if form_data.get('contact_phone'):
            parts.append(form_data['contact_phone'])

        contact_content = [
            [Paragraph("Your Anura Connect Contact", styles['contact_title'])],
            [Paragraph("  \u2502  ".join(parts), styles['contact_info'])],
            [Paragraph("Reach out with any questions before your interview \u2014 we're here to help you succeed.",
                        styles['contact_cta'])],
        ]
        contact_box = Table(contact_content, colWidths=[content_width])
        contact_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
            ('BOX', (0, 0), (-1, -1), 0.75, LIGHT_BLUE_2),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (0, 0), 16),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ]))
        story.append(contact_box)

    # Build
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
