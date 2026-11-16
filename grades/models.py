from django.conf import settings
from django.db import models
from django.db.models import Avg, F


class Grade(models.Model):
    class Kind(models.TextChoices):
        DEVOIR = "DEVOIR", "Devoir"
        CONTROLE = "CONTROLE", "Contrôle"
        EXAMEN = "EXAMEN", "Examen"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="grades", verbose_name="Élève")
    class_subject = models.ForeignKey("academics.ClassSubject", on_delete=models.CASCADE, related_name="grades", verbose_name="Matière de classe")
    period = models.ForeignKey("academics.Period", on_delete=models.CASCADE, related_name="grades", verbose_name="Période")
    kind = models.CharField("Type", max_length=10, choices=Kind.choices, default=Kind.DEVOIR)
    score = models.DecimalField("Note (/20)", max_digits=4, decimal_places=2)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="grades_entered", verbose_name="Saisi par",
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.full_name} - {self.class_subject.subject.name} : {self.score}/20"

    @classmethod
    def subject_average(cls, student, class_subject, period):
        return cls.objects.filter(
            student=student, class_subject=class_subject, period=period
        ).aggregate(avg=Avg("score"))["avg"]

    @classmethod
    def general_average(cls, student, period):
        classroom = student.classroom
        if not classroom:
            return None
        total_points = 0
        total_coef = 0
        for cs in classroom.subjects.all():
            avg = cls.subject_average(student, cs, period)
            if avg is not None:
                total_points += float(avg) * cs.coefficient
                total_coef += cs.coefficient
        return round(total_points / total_coef, 2) if total_coef else None

    @classmethod
    def class_ranking(cls, classroom, period):
        students = list(classroom.students.filter(status="ACTIF"))
        ranked = []
        for s in students:
            avg = cls.general_average(s, period)
            if avg is not None:
                ranked.append((s, avg))
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        return [(i + 1, s, avg) for i, (s, avg) in enumerate(ranked)]
