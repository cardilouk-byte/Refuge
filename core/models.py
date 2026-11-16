from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")


def validate_pdf_size(pdf):
    if pdf.size > 10 * 1024 * 1024:
        raise ValidationError("Le fichier PDF ne doit pas dépasser 10 Mo.")


class SiteSettings(models.Model):
    name = models.CharField("Nom complet de l'école", max_length=200)
    short_name = models.CharField("Nom court", max_length=20, default="LNFCL")
    logo = models.ImageField(
        "Logo", upload_to="site/", blank=True, null=True,
        validators=[validate_image_size, FileExtensionValidator(["png", "jpg", "jpeg", "webp", "svg"])],
    )
    motto = models.CharField("Devise", max_length=200, default="S'instruire pour mieux servir")
    address = models.CharField("Adresse", max_length=255, blank=True)
    phone = models.CharField("Téléphone", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    whatsapp_url = models.URLField("WhatsApp", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    google_maps_url = models.URLField("Lien Google Maps", blank=True)
    primary_color = models.CharField("Couleur principale", max_length=7, default="#0d6efd")
    copyright_text = models.CharField("Copyright", max_length=200, blank=True)
    hero_overlay_opacity = models.PositiveIntegerField(
        "Opacité de la couche bleue du hero (%)", default=55, help_text="0 à 90"
    )
    slider_interval = models.PositiveIntegerField(
        "Vitesse du slider (secondes)", default=6
    )
    seo_title = models.CharField("Titre SEO", max_length=200, blank=True)
    seo_description = models.TextField("Description SEO", blank=True)
    favicon = models.ImageField(
        "Favicon", upload_to="site/", blank=True, null=True,
        validators=[validate_image_size, FileExtensionValidator(["png", "jpg", "jpeg", "ico", "webp"])],
    )

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MenuItem(models.Model):
    label = models.CharField("Libellé", max_length=100)
    url = models.CharField("Lien", max_length=255, help_text="Ex: /#apropos ou /resultats/")
    order = models.PositiveIntegerField("Ordre", default=0)
    is_visible = models.BooleanField("Affiché", default=True)

    class Meta:
        verbose_name = "Élément de menu"
        verbose_name_plural = "Éléments de menu"
        ordering = ["order"]

    def __str__(self):
        return self.label


class HeroSlide(models.Model):
    title = models.CharField("Titre", max_length=200)
    subtitle = models.CharField("Sous-titre / devise", max_length=200, blank=True)
    image = models.ImageField("Image de fond", upload_to="hero/", validators=[validate_image_size])
    button_text = models.CharField("Texte du bouton", max_length=100, default="Lire Plus")
    button_url = models.CharField("Lien du bouton", max_length=255, default="/#apropos")
    order = models.PositiveIntegerField("Ordre", default=0)
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Slide héro"
        verbose_name_plural = "Slides héro"
        ordering = ["order"]

    def __str__(self):
        return self.title


class About(models.Model):
    title = models.CharField("Titre", max_length=200, default="À Propos de nous")
    text = models.TextField("Texte de présentation")
    image = models.ImageField("Image", upload_to="about/", blank=True, null=True, validators=[validate_image_size])
    stat_students = models.PositiveIntegerField("Nombre d'élèves", default=0)
    stat_teachers = models.PositiveIntegerField("Nombre de professeurs", default=0)
    stat_years = models.PositiveIntegerField("Années d'existence", default=0)
    stat_graduates = models.PositiveIntegerField("Diplômés", default=0)
    director_name = models.CharField("Nom du directeur", max_length=150, blank=True)
    director_photo = models.ImageField("Photo du directeur", upload_to="about/", blank=True, null=True, validators=[validate_image_size])
    director_message = models.TextField("Message du directeur", blank=True)
    mission = models.TextField("Mission", blank=True)
    vision = models.TextField("Vision", blank=True)
    values = models.TextField("Valeurs", blank=True)

    class Meta:
        verbose_name = "À Propos"
        verbose_name_plural = "À Propos"

    def __str__(self):
        return self.title


class Service(models.Model):
    title = models.CharField("Titre", max_length=150)
    description = models.TextField("Description")
    icon = models.CharField(
        "Icône (Bootstrap Icons)", max_length=100, default="bi-mortarboard",
        help_text="Ex: bi-mortarboard, bi-book, bi-people-fill",
    )
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ["order"]

    def __str__(self):
        return self.title


class Program(models.Model):
    LEVELS = [
        ("Fondamental", "Fondamental"),
        ("Secondaire", "Secondaire"),
        ("Nouveau Secondaire", "Nouveau Secondaire"),
        ("Autre", "Autre"),
    ]
    name = models.CharField("Nom", max_length=150)
    description = models.TextField("Description")
    image = models.ImageField("Image", upload_to="programmes/", blank=True, null=True, validators=[validate_image_size])
    level = models.CharField("Niveau", max_length=50, choices=LEVELS, default="Fondamental")
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Programme"
        verbose_name_plural = "Programmes"
        ordering = ["order"]

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    title = models.CharField("Titre", max_length=150, blank=True)
    category = models.CharField("Catégorie", max_length=100, default="Général")
    image = models.ImageField("Image", upload_to="galerie/", validators=[validate_image_size])
    date = models.DateField("Date", auto_now_add=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Image de galerie"
        verbose_name_plural = "Images de galerie"
        ordering = ["order", "-date"]

    def __str__(self):
        return self.title or f"Image #{self.pk}"


class Result(models.Model):
    title = models.CharField("Titre", max_length=200)
    school_year = models.CharField("Année scolaire", max_length=20, help_text="Ex: 2024-2025")
    pdf_file = models.FileField(
        "Fichier PDF", upload_to="resultats/",
        validators=[validate_pdf_size, FileExtensionValidator(["pdf"])],
    )
    published_at = models.DateTimeField("Date de publication", auto_now_add=True)
    is_public = models.BooleanField("Public (sinon réservé aux connectés)", default=True)

    class Meta:
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.title} ({self.school_year})"


class NewsEvent(models.Model):
    title = models.CharField("Titre", max_length=200)
    image = models.ImageField("Image", upload_to="nouveles/", blank=True, null=True, validators=[validate_image_size])
    body = models.TextField("Texte")
    date = models.DateField("Date", auto_now_add=True)
    is_published = models.BooleanField("Publié", default=True)

    class Meta:
        verbose_name = "Nouvelle / Événement"
        verbose_name_plural = "Nouvelles / Événements"
        ordering = ["-date"]

    def __str__(self):
        return self.title


class TeamMember(models.Model):
    name = models.CharField("Nom", max_length=150)
    photo = models.ImageField("Photo", upload_to="equipe/", blank=True, null=True, validators=[validate_image_size])
    position = models.CharField("Position", max_length=150)
    subjects = models.CharField("Matières", max_length=255, blank=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Membre de l'équipe"
        verbose_name_plural = "Équipe / Professeurs"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    name = models.CharField("Nom", max_length=150)
    email = models.EmailField("Email")
    subject = models.CharField("Sujet", max_length=200)
    message = models.TextField("Message")
    created_at = models.DateTimeField("Date", auto_now_add=True)
    is_read = models.BooleanField("Lu", default=False)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"
