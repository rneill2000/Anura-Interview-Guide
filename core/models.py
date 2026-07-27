from django.db import models


class GeneratedGuide(models.Model):
    """Every finalized guide, stored permanently: the PDF itself plus the
    form details that produced it, so any past guide can be re-downloaded
    or loaded back into the form for edits — even after redeploys."""

    candidate_name = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=300, blank=True)
    health_system_name = models.CharField(max_length=300, blank=True)
    filename = models.CharField(max_length=300)
    pdf = models.BinaryField()
    form_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = self.candidate_name or "General"
        return f"{who} — {self.job_title} ({self.created_at:%Y-%m-%d})"


class GuideTemplate(models.Model):
    """A reusable, named snapshot of the guide form — everything EXCEPT
    candidate-specific details (name, resume, fit analysis), so one template
    can serve many candidates for the same role/health system.

    The form fields are stored as a JSON payload rather than individual
    columns so the template survives future form changes without migrations.
    """

    name = models.CharField(max_length=200, unique=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name
