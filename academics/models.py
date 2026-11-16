from django.db import models


class SchoolYear(models.Model):
    label = models.CharField("Libellé", max_length=20, help_text="Ex: 2025-2026")
    is_current = models.BooleanField("Année en cours", default=False)

    class Meta:
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"
        ordering = ["-label"]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if self.is_current:
            SchoolYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Cycle(models.Model):
    name = models.CharField("Nom", max_length=50)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Cycle"
        verbose_name_plural = "Cycles"
        ordering = ["order"]

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField("Nom", max_length=50, help_text="Ex: 6ème AF, NS1, Préscolaire")
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name="levels", verbose_name="Cycle")
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"
        ordering = ["order"]

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name="classrooms", verbose_name="Année scolaire")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="classrooms", verbose_name="Niveau")
    section = models.CharField("Section", max_length=20, default="A")
    main_teacher = models.ForeignKey(
        "teachers.Teacher", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="main_classrooms", verbose_name="Professeur titulaire",
    )

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["school_year", "level__order", "section"]
        unique_together = ["school_year", "level", "section"]

    def __str__(self):
        return f"{self.level.name} {self.section} ({self.school_year.label})"

    @property
    def name(self):
        return f"{self.level.name} {self.section}"


class Period(models.Model):
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name="periods", verbose_name="Année scolaire")
    name = models.CharField("Nom", max_length=50, help_text="Ex: Trimestre 1")
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Période"
        verbose_name_plural = "Périodes"
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.school_year.label})"


class Subject(models.Model):
    name = models.CharField("Nom", max_length=100)
    code = models.CharField("Code", max_length=20, blank=True)

    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClassSubject(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="subjects", verbose_name="Classe")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_assignments", verbose_name="Matière")
    teacher = models.ForeignKey(
        "teachers.Teacher", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="assignments", verbose_name="Professeur",
    )
    coefficient = models.PositiveIntegerField("Coefficient", default=1)
    weekly_hours = models.PositiveIntegerField("Heures/semaine", default=2)

    class Meta:
        verbose_name = "Matière de classe"
        verbose_name_plural = "Matières par classe"
        unique_together = ["classroom", "subject"]
        ordering = ["classroom", "subject__name"]

    def __str__(self):
        return f"{self.classroom.name} - {self.subject.name}"


class ScheduleSlot(models.Model):
    WEEKDAYS = [
        (1, "Lundi"), (2, "Mardi"), (3, "Mercredi"),
        (4, "Jeudi"), (5, "Vendredi"), (6, "Samedi"),
    ]
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name="slots", verbose_name="Matière de classe")
    weekday = models.IntegerField("Jour", choices=WEEKDAYS)
    start_time = models.TimeField("Heure de début")
    end_time = models.TimeField("Heure de fin")
    room = models.CharField("Local", max_length=50, blank=True)

    class Meta:
        verbose_name = "Créneau d'emploi du temps"
        verbose_name_plural = "Emploi du temps"
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.class_subject} - {self.get_weekday_display()} {self.start_time:%H:%M}"
