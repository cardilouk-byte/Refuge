from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")


def validate_pdf_size(pdf):
    if pdf.size > 10 * 1024 * 1024:
        raise ValidationError("Le fichier PDF ne doit pas dépasser 10 Mo.")


FONT_CHOICES = [
    ("Lobster", "Lobster (kursif)"),
    ("Poppins", "Poppins"),
    ("Montserrat", "Montserrat"),
    ("Playfair Display", "Playfair Display"),
    ("Dancing Script", "Dancing Script (kursif)"),
    ("Oswald", "Oswald"),
    ("Roboto", "Roboto"),
    ("Open Sans", "Open Sans"),
    ("Merriweather", "Merriweather"),
]


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
    header_bg_color = models.CharField("Couleur de fond du header", max_length=7, default="#ffffff")
    header_text_color = models.CharField("Couleur du texte du header", max_length=7, default="#1f2937")
    footer_bg_color = models.CharField("Couleur de fond du footer", max_length=7, default="#1f2937")
    footer_text_color = models.CharField("Couleur du texte du footer", max_length=7, default="#ffffff")
    title_font = models.CharField("Police des titres", max_length=50, choices=FONT_CHOICES, default="Lobster")
    body_font = models.CharField("Police du texte", max_length=50, choices=FONT_CHOICES, default="Poppins")
    marquee_enabled = models.BooleanField("Barre de texte défilant activée", default=False)
    marquee_text = models.CharField("Texte défilant", max_length=300, blank=True)
    marquee_speed = models.PositiveIntegerField("Vitesse du texte défilant (secondes)", default=20, help_text="Durée d'un cycle complet")
    aos_duration = models.PositiveIntegerField("Durée des animations (ms)", default=800)
    show_hero = models.BooleanField("Afficher le hero (slider)", default=True)
    show_about = models.BooleanField("Afficher la section À Propos", default=True)
    show_services = models.BooleanField("Afficher la section Services", default=True)
    show_programs = models.BooleanField("Afficher la section Programmes", default=True)
    show_gallery = models.BooleanField("Afficher la section Galerie", default=True)
    show_news = models.BooleanField("Afficher la section Nouvelles", default=True)
    show_team = models.BooleanField("Afficher la section Équipe", default=True)
    show_contact = models.BooleanField("Afficher la section Contact", default=True)
    copyright_text = models.CharField("Copyright", max_length=200, blank=True)
    hero_overlay_opacity = models.PositiveIntegerField(
        "Opacité de la couche bleue du hero (%)", default=55, help_text="0 à 90"
    )
    slider_interval = models.PositiveIntegerField(
        "Vitesse du slider (secondes)", default=6
    )
    SLIDER_EFFECTS = [
        ("fade", "Fondu (fade)"),
        ("slide", "Glisad (slide)"),
        ("zoom", "Zoom"),
        ("flip", "Flip 3D"),
    ]
    slider_effect = models.CharField(
        "Effet de transition du slider", max_length=20,
        choices=SLIDER_EFFECTS, default="fade",
    )
    slider_autoplay = models.BooleanField("Défilement automatique du slider", default=True)
    SECTION_ANIMATIONS = [
        ("fade-up", "Monte (fade-up)"),
        ("fade-down", "Desann (fade-down)"),
        ("fade-left", "Soti adwat (fade-left)"),
        ("fade-right", "Soti agoch (fade-right)"),
        ("zoom-in", "Zoom anndan (zoom-in)"),
        ("flip-left", "Flip agoch"),
        ("flip-up", "Flip anlè"),
    ]
    section_animation = models.CharField(
        "Animation des sections", max_length=20,
        choices=SECTION_ANIMATIONS, default="fade-up",
    )
    HERO_POSITIONS = [
        ("left", "Agòch"),
        ("center", "Nan mitan"),
        ("right", "Adwat"),
    ]
    hero_text_position = models.CharField(
        "Position du texte du hero", max_length=10,
        choices=HERO_POSITIONS, default="left",
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
    image = models.ImageField("Image de fond", upload_to="hero/", blank=True, null=True, validators=[validate_image_size])
    video = models.FileField(
        "Vidéo de fond", upload_to="hero/", blank=True, null=True,
        validators=[FileExtensionValidator(["mp4", "webm", "ogg"])],
        help_text="Si une vidéo est fournie, elle remplace l'image de fond.",
    )
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
    image = models.ImageField("Image", upload_to="galerie/", blank=True, null=True, validators=[validate_image_size])
    video = models.FileField(
        "Vidéo (fichier)", upload_to="galerie/", blank=True, null=True,
        validators=[FileExtensionValidator(["mp4", "webm", "ogg"])],
    )
    video_url = models.URLField("Vidéo (lien YouTube)", blank=True, help_text="Ex: https://www.youtube.com/watch?v=...")
    date = models.DateField("Date", auto_now_add=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Image de galerie"
        verbose_name_plural = "Images de galerie"
        ordering = ["order", "-date"]

    def __str__(self):
        return self.title or f"Image #{self.pk}"

    @property
    def video_embed_url(self):
        url = self.video_url
        if "youtube.com/watch" in url and "v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        if "youtu.be/" in url:
            return url.replace("youtu.be/", "www.youtube.com/embed/")
        return url


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
