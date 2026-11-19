from django.conf import settings
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="Destinataire",
    )
    title = models.CharField("Tit", max_length=200)
    body = models.TextField("Konekte", blank=True)
    url = models.CharField("Lyen", max_length=300, blank=True)
    is_read = models.BooleanField("Li", default=False)
    created_at = models.DateTimeField("Kreye le", auto_now_add=True)

    class Meta:
        verbose_name = "Notifikasyon"
        verbose_name_plural = "Notifikasyon"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} — {self.title}"

    @classmethod
    def send(cls, recipient, title, body="", url=""):
        if recipient is None:
            return None
        return cls.objects.create(recipient=recipient, title=title, body=body, url=url)

    @classmethod
    def send_many(cls, recipients, title, body="", url=""):
        objs = [
            cls(recipient=r, title=title, body=body, url=url)
            for r in recipients if r is not None
        ]
        if objs:
            cls.objects.bulk_create(objs)
