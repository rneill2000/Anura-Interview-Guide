from django.db import models


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
