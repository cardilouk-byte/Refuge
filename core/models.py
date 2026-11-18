from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def validate_image_size(image):
    if image.size > 15 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 15 Mo.")


def validate_video_size(video):
    if video.size > 150 * 1024 * 1024:
        raise ValidationError("La vidéo ne doit pas dépasser 150 Mo.")


def compress_image_file(field_file, max_size=1600, quality=82):
    from PIL import Image
    from django.core.files.base import ContentFile

    raw = getattr(field_file, "file", field_file)
    try:
        img = Image.open(raw)
        img.load()
    except Exception:
        return field_file
    if img.mode in ("RGBA", "P", "LA"):
        return field_file
    if max(img.size) <= max_size:
        return field_file
    img.thumbnail((max_size, max_size))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    base_name = field_file.name.rsplit(".", 1)[0]
    new_file = ContentFile(buffer.getvalue(), name=f"{base_name}.jpg")
    return new_file


class CompressedImagesMixin(models.Model):
    IMAGE_FIELDS = []

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for name in self.IMAGE_FIELDS:
            field_file = getattr(self, name, None)
            if field_file and not getattr(field_file, "_committed", True):
                setattr(self, name, compress_image_file(field_file))
        super().save(*args, **kwargs)


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
    show_school_life = models.BooleanField("Afficher la section Vie scolaire (klib / espò)", default=True)
    show_testimonials = models.BooleanField("Afficher la section Témoignages", default=True)
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
    hashtag = models.CharField("Hashtag (marque sociale)", max_length=60, blank=True, default="#LNFCLOuvè")
    inspire_texts = models.TextField(
        "Déclarations d'inspiration (une phrase par ligne)", blank=True,
        help_text="Ex: La pou w kifikou\nLa pou w dekouvri pasyon w",
    )
    admission_intro = models.TextField("Tèks entwodiksyon paj enskripsyon", blank=True)
    seo_title = models.CharField("Titre SEO", max_length=200, blank=True)
    seo_description = models.TextField("Description SEO", blank=True)
    favicon = models.ImageField(
        "Favicon", upload_to="site/", blank=True, null=True,
        validators=[validate_image_size, FileExtensionValidator(["png", "jpg", "jpeg", "ico", "webp"])],
    )
    site_actif = models.BooleanField(
        "Site actif", default=True,
        help_text="Si décoché, seuls les administrateurs voient le site ; tout le monde voit la page de maintenance.",
    )
    message_maintenance = models.TextField(
        "Message de maintenance", blank=True,
        default="Sit la gen reparasyon kounye a. Tanpri tounen pi pita. Mèsi!",
    )
    DEGRADE_PRESETS = {
        "ocean": ("#0f2a63", "#0ea5e9"),
        "coucher_soleil": ("#f97316", "#db2777"),
        "foret": ("#14532d", "#22c55e"),
        "violet_royal": ("#4c1d95", "#7c3aed"),
        "rose_dore": ("#be123c", "#f59e0b"),
        "nuit": ("#0f172a", "#1e3a8a"),
    }
    DEGRADE_STYLES = [
        ("personnalise", "Pèrsonalizé (koulè mwen yo)"),
        ("ocean", "Ble oseyan"),
        ("coucher_soleil", "Kouche solèy"),
        ("foret", "Fòè"),
        ("violet_royal", "Vwayèt woyal"),
        ("rose_dore", "Woz dore"),
        ("nuit", "Nwi etwalè"),
    ]
    degrade_actif = models.BooleanField(
        "Utiliser un dégradé pour l'en-tête", default=False,
        help_text="Si coché, l'en-tête utilise un dégradé de deux couleurs au lieu d'une couleur unie.",
    )
    degrade_style = models.CharField(
        "Style de dégradé", max_length=20,
        choices=DEGRADE_STYLES, default="personnalise",
    )
    degrade_debut = models.CharField("Dégradé — couleur de départ", max_length=7, default="#0f2a63")
    degrade_fin = models.CharField("Dégradé — couleur de fin", max_length=7, default="#0ea5e9")
    degrade_angle = models.PositiveSmallIntegerField(
        "Dégradé — angle (°)", default=135,
        help_text="0° = du bas vers le haut, 90° = de gauche à droite, 135° = diagonale.",
    )
    HERO_ANIMATIONS = [
        ("aucune", "Okenn"),
        ("degrade_anime", "Dégradé animé (mouvement lent)"),
        ("flottant", "Fòm flottantes"),
        ("particules", "Patikil"),
        ("zoom_lent", "Zoom lent (effet Ken Burns)"),
    ]
    hero_animation = models.CharField(
        "Animation du bandeau d'accueil", max_length=20,
        choices=HERO_ANIMATIONS, default="aucune",
    )
    STYLE_COINS = [
        ("arrondis", "Awondi (modèn)"),
        ("tres_arrondis", "Trè awondi (dous)"),
        ("carres", "Karè (sòb)"),
    ]
    style_coins = models.CharField(
        "Style des coins (boutons, cartes)", max_length=20,
        choices=STYLE_COINS, default="arrondis",
    )
    activer_animations = models.BooleanField(
        "Activer les animations", default=True,
        help_text="Active les animations d'apparition, de survol et de transition sur tout le site.",
    )
    footer_logo_1 = models.ImageField(
        "Logo du pied de page (1)", upload_to="site/footer/", blank=True, null=True,
        validators=[validate_image_size],
    )
    footer_logo_2 = models.ImageField(
        "Logo du pied de page (2)", upload_to="site/footer/", blank=True, null=True,
        validators=[validate_image_size],
    )
    footer_logo_3 = models.ImageField(
        "Logo du pied de page (3)", upload_to="site/footer/", blank=True, null=True,
        validators=[validate_image_size],
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
    parent = models.ForeignKey(
        "self", verbose_name="Meni paran (sous-men)", on_delete=models.CASCADE,
        null=True, blank=True, related_name="children",
        limit_choices_to={"parent__isnull": True},
    )
    order = models.PositiveIntegerField("Ordre", default=0)
    is_visible = models.BooleanField("Affiché", default=True)

    class Meta:
        verbose_name = "Élément de menu"
        verbose_name_plural = "Éléments de menu"
        ordering = ["order"]

    def __str__(self):
        return self.label


class HeroSlide(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image"]
    title = models.CharField("Titre", max_length=200)
    subtitle = models.CharField("Sous-titre / devise", max_length=200, blank=True)
    image = models.ImageField("Image de fond", upload_to="hero/", blank=True, null=True, validators=[validate_image_size])
    video = models.FileField(
        "Vidéo de fond", upload_to="hero/", blank=True, null=True,
        validators=[FileExtensionValidator(["mp4", "webm", "ogg", "mov", "m4v"]), validate_video_size],
        help_text="Si une vidéo est fournie, elle remplace l'image de fond. Format pi bon: MP4.",
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


class About(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image", "director_photo"]
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
    history = models.TextField("Istwa lekòl la", blank=True)

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


class Program(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image"]
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


class GalleryImage(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image"]
    title = models.CharField("Titre", max_length=150, blank=True)
    category = models.CharField("Catégorie", max_length=100, default="Général")
    image = models.ImageField("Image", upload_to="galerie/", blank=True, null=True, validators=[validate_image_size])
    video = models.FileField(
        "Vidéo (fichier)", upload_to="galerie/", blank=True, null=True,
        validators=[FileExtensionValidator(["mp4", "webm", "ogg", "mov", "m4v"]), validate_video_size],
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


class NewsEvent(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image"]
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


class TeamMember(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["photo"]
    name = models.CharField("Nom", max_length=150)
    photo = models.ImageField("Photo", upload_to="equipe/", blank=True, null=True, validators=[validate_image_size])
    position = models.CharField("Position", max_length=150)
    subjects = models.CharField("Matières", max_length=255, blank=True)
    email = models.EmailField("Email", blank=True)
    bio = models.TextField("Biographie", blank=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Membre de l'équipe"
        verbose_name_plural = "Équipe / Professeurs"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Testimonial(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["photo"]
    name = models.CharField("Nom", max_length=120)
    class_name = models.CharField("Klas / Pozisyon", max_length=100, blank=True)
    quote = models.TextField("Témoignage")
    photo = models.ImageField("Photo", upload_to="temwayaj/", blank=True, null=True, validators=[validate_image_size])
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Club(CompressedImagesMixin, models.Model):
    IMAGE_FIELDS = ["image"]
    CATEGORIES = [
        ("KLUB", "Klib"),
        ("ESPO", "Espò"),
        ("AKTIVITE", "Aktivite"),
        ("ATIZANAL", "Atizana"),
        ("LOT", "Lòt"),
    ]
    name = models.CharField("Nom", max_length=150)
    category = models.CharField("Catégorie", max_length=20, choices=CATEGORIES, default="KLUB")
    description = models.TextField("Description")
    supervisor = models.CharField("Pwofesè responsab", max_length=150, blank=True)
    schedule = models.CharField("Joun / lè", max_length=150, blank=True)
    image = models.ImageField("Image", upload_to="klib/", blank=True, null=True, validators=[validate_image_size])
    is_active = models.BooleanField("Actif", default=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Klib / Aktivite"
        verbose_name_plural = "Klib & Aktivite"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class SchoolEvent(models.Model):
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", blank=True)
    location = models.CharField("Lieu", max_length=200, blank=True)
    date = models.DateField("Date")
    end_date = models.DateField("Date de fin (facultatif)", null=True, blank=True)
    is_published = models.BooleanField("Publié", default=True)

    class Meta:
        verbose_name = "Événement (calendrier)"
        verbose_name_plural = "Événements (calendrier)"
        ordering = ["date"]

    def __str__(self):
        return "{} ({})".format(self.title, self.date)


class FAQ(models.Model):
    question = models.CharField("Question", max_length=250)
    answer = models.TextField("Réponse")
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


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
