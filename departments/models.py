from django.conf import settings
from django.db import models


class Department(models.Model):
    KINDS = [
        ("DIRECTION", "Direction"),
        ("ADMINISTRATION", "Administration"),
        ("PEDAGOGIQUE", "Pédagogique"),
        ("APPUI", "Appui / Service"),
    ]
    name = models.CharField("Nom du département", max_length=150)
    code = models.CharField("Code", max_length=20, blank=True)
    kind = models.CharField("Type", max_length=20, choices=KINDS, default="APPUI")
    parent = models.ForeignKey(
        "self", verbose_name="Département parent", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="children",
    )
    head_title = models.CharField("Titre du responsable", max_length=100, blank=True, help_text="Ex: Directeur, Bibliothécaire")
    description = models.TextField("Description", blank=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=50, blank=True)
    location = models.CharField("Localisation", max_length=150, blank=True, help_text="Ex: Bâtiment A, 2e étage")
    order = models.PositiveIntegerField("Ordre", default=0)
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    @property
    def depth(self):
        level = 0
        node = self.parent
        while node is not None and level < 10:
            level += 1
            node = node.parent
        return level

    def descendants_ids(self):
        ids = []
        stack = [self.pk]
        while stack:
            current = stack.pop()
            children = Department.objects.filter(parent_id=current).values_list("pk", flat=True)
            for child in children:
                ids.append(child)
                stack.append(child)
        return ids


class StaffPosition(models.Model):
    department = models.ForeignKey(
        Department, verbose_name="Département", on_delete=models.CASCADE, related_name="positions",
    )
    title = models.CharField("Fonction", max_length=100, help_text="Ex: Directeur, Secrétaire, Bibliothécaire")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur (compte)", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="staff_positions",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher", verbose_name="Professeur", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="staff_positions",
    )
    external_name = models.CharField("Nom (si pas de compte)", max_length=150, blank=True)
    is_head = models.BooleanField("Responsable du département", default=False)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Poste du personnel"
        verbose_name_plural = "Postes du personnel"
        ordering = ["-is_head", "order"]

    def __str__(self):
        return f"{self.title} — {self.person_name} ({self.department.name})"

    @property
    def person_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        if self.teacher:
            return f"{self.teacher.first_name} {self.teacher.last_name}"
        return self.external_name or "—"
