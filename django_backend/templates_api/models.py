from django.conf import settings
from django.db import models


class EmailHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_history",
    )
    template_id = models.CharField(max_length=64)
    template_name = models.CharField(max_length=150)
    recipient_company = models.CharField(max_length=150)
    inserted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inserted_at", "-id"]

