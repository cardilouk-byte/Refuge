from django.conf import settings
from django.db import models


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Présent"
        ABSENT = "ABSENT", "Absent"
        RETARD = "RETARD", "Retard"

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE,
        related_name="attendance_records", verbose_name="Élève",
    )
    date = models.DateField("Date")
    status = models.CharField("Statut", max_length=10, choices=Status.choices, default=Status.PRESENT)
    justified = models.BooleanField("Absence justifiée", default=False)
    note = models.CharField("Remarque", max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="attendance_recorded", verbose_name="Enregistré par",
    )

    class Meta:
        verbose_name = "Présence / Absence"
        verbose_name_plural = "Présences / Absences"
        ordering = ["-date"]
        unique_together = ["student", "date"]

    def __str__(self):
        return f"{self.student.full_name} - {self.date} : {self.get_status_display()}"
