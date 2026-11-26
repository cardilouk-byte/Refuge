from django.conf import settings
from django.db import models


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="messages_sent", verbose_name="Expéditeur",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="messages_received", verbose_name="Destinataire",
    )
    subject = models.CharField("Sujet", max_length=200)
    body = models.TextField("Message")
    created_at = models.DateTimeField("Envoyé le", auto_now_add=True)
    read_at = models.DateTimeField("Lu le", blank=True, null=True)

    class Meta:
        verbose_name = "Message interne"
        verbose_name_plural = "Messages internes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.sender} → {self.recipient}"

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        from django.utils import timezone
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])
