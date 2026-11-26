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
    def latest_exam(cls, student, class_subject):
        return cls.objects.filter(
            student=student, class_subject=class_subject, kind=cls.Kind.EXAMEN
        ).order_by("created_at").first()

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


class CarnetSettings(models.Model):
    """Mod\u00e8l karn\u00e8 lek\u00f2l la \u2014 tout t\u00e8 kouv\u00e8ti a ki modifye anvan enpresyon."""

    school_name = models.CharField(
        "Nom lek\u00f2l la (kouv\u00e8ti)", max_length=200,
        default="Lyc\u00e9e National Fran\u00e7ois Cappoix de Limonade",
    )
    slogan = models.CharField(
        "Slogan", max_length=200, default="VERS L'EXCELLENCE !",
    )
    subtitle = models.CharField(
        "Sous-tit kouv\u00e8ti", max_length=200, default="Carnet Scolaire",
        help_text="Ex: Carnet Scolaire \u2014 3e cycle fond. et secondaire",
    )
    address = models.CharField("Adr\u00e8s", max_length=255, default="Limonade, Ha\u00efti")
    tel1 = models.CharField("Telef\u00f2n 1", max_length=60, blank=True)
    tel2 = models.CharField("Telef\u00f2n 2", max_length=60, blank=True)
    email = models.EmailField("Email", blank=True)
    footer_motto = models.CharField(
        "Deviz anba paj", max_length=200,
        default="LNFCL c'est l'excellence plus que la qualit\u00e9 !",
    )
    reglements_text = models.TextField(
        "Ekstra r\u00e8gman ent\u00e8n", default=(
            "1.Entr\u00e9e des \u00e9l\u00e8ves \u00e0 7h30 pr\u00e9cises.\n"
            "2.Tout retard constitue une faute sanctionn\u00e9e.\n"
            "3.Le port de l'uniforme est obligatoire.\n"
            "4.Le bulletin doit \u00eatre sign\u00e9 par le parent dans les 2 jours.\n"
            "5.Toute d\u00e9gradation du mobilier sera factur\u00e9e.\n"
            "6.Le carnet doit \u00eatre conserv\u00e9 en bon \u00e9tat pendant toute l'ann\u00e9e.\n"
            "7.Manquement grave : renvoi temporaire ou d\u00e9finitif."
        ),
    )
    show_graph = models.BooleanField(
        "Afiche graf (NS4 / 9e AF)", default=True,
    )
    directeur = models.CharField(
        "Nom du Directeur", max_length=150, default="Le Directeur G\u00e9n\u00e9ral",
        help_text="Ki ap siyen k\u00f2t Direksyon an nan karn\u00e8 a.",
    )
    border_color = models.CharField(
        "Koul\u00e8 kadajy\u00e8 paj yo", max_length=7, default="#1f2937",
    )
    cover_bg = models.CharField(
        "Koul\u00e8 fon kouv\u00e8ti", max_length=7, default="#166534",
        help_text="Koul\u00e8 tout fon kouv\u00e8ti devan an.",
    )
    cover_text = models.CharField(
        "Koul\u00e8 t\u00e8ks kouv\u00e8ti", max_length=7, default="#ffffff",
    )
    header_color = models.CharField(
        "Koul\u00e8 mod entery\u00e8 (bando + t\u00e8t tab)", max_length=7, default="#166534",
    )
    show_photo = models.BooleanField(
        "Afiche foto el\u00e8v la sou kouv\u00e8ti a", default=True,
    )
    updated_at = models.DateTimeField("Dènye modifikasyon", auto_now=True)

    class Meta:
        verbose_name = "Mod\u00e8l karn\u00e8"
        verbose_name_plural = "Mod\u00e8l karn\u00e8"

    def __str__(self):
        return self.subtitle

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
