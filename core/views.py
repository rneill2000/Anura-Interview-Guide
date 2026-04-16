import os
import uuid
import threading

from django.shortcuts import render, redirect
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods

from guide_generator.generator import generate_interview_guide, DEFAULT_INTERVIEW_TIPS, _generate_recent_news
from guide_generator.pdf_builder import build_guide_pdf

# Simple in-memory status tracker (same pattern as Resume Tool)
_generation_status = {}
_generation_lock = threading.Lock()


def index(request):
    """Main form page."""
    return render(request, "index.html", {
        "default_tips": "\n".join(DEFAULT_INTERVIEW_TIPS),
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
    }

    # Validate required fields
    required = ["candidate_name", "job_title", "job_description", "health_system_name"]
    missing = [f for f in required if not form_data[f]]
    if missing:
        return render(request, "index.html", {
            "error": f"Please fill in: {', '.join(missing)}",
            "form_data": form_data,
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
