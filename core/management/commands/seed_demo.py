import random
from io import BytesIO

from PIL import Image, ImageDraw
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from datetime import date, timedelta

from django.utils import timezone

from core.models import (
    About, Club, FAQ, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program,
    Result, SchoolEvent, Service, SiteSettings, TeamMember, Testimonial,
)

PALETTE = [(13, 110, 253), (10, 88, 202), (29, 78, 216), (3, 105, 161), (67, 56, 202)]


def gradient_image(width, height, color, label=""):
    top = color
    bottom = tuple(max(0, c - 60) for c in color)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        blended = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=blended)
    if label:
        draw.text((width // 2 - 60, height // 2), label, fill=(255, 255, 255))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=82)
    return ContentFile(buffer.getvalue())


def minimal_pdf(title):
    stream = (
        "BT /F1 18 Tf 60 720 Td (LNFCL - Resultats) Tj ET\n"
        f"BT /F1 12 Tf 60 690 Td ({title}) Tj ET"
    )
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    ).encode()
    return ContentFile(pdf)


class Command(BaseCommand):
    help = "Remplit la base avec un contenu de démonstration pour LNFCL."

    def handle(self, *args, **options):
        random.seed(42)

        settings_obj = SiteSettings.load()
        settings_obj.name = "Lycée National François Cappoix de Limonade"
        settings_obj.short_name = "LNFCL"
        settings_obj.motto = "S'instruire pour mieux servir"
        settings_obj.address = "Limonade, Cap-Haïtien, Haïti"
        settings_obj.phone = "+509 37 00 0000"
        settings_obj.email = "contact@lnfcl.edu.ht"
        settings_obj.facebook_url = "https://facebook.com/lnfcl"
        settings_obj.youtube_url = "https://youtube.com/@lnfcl"
        settings_obj.whatsapp_url = "https://wa.me/50937000000"
        settings_obj.instagram_url = "https://instagram.com/lnfcl"
        settings_obj.google_maps_url = (
            "https://www.google.com/maps?q=Limonade,+Cap-Ha%C3%AFtien,+Ha%C3%AFti&output=embed"
        )
        settings_obj.copyright_text = "© 2026 LNFCL - Tous droits réservés."
        settings_obj.seo_title = "LNFCL - Lycée National François Cappoix de Limonade"
        settings_obj.seo_description = (
            "Site officiel du Lycée National François Cappoix de Limonade : "
            "programmes, résultats scolaires, galerie et contact."
        )
        settings_obj.save()
        self.stdout.write("OK SiteSettings")

        MenuItem.objects.all().delete()
        menu = [
            ("Accueil", "/#accueil"), ("À Propos", "/#apropos"),
            ("Services", "/#services"), ("Galerie", "/#galerie"),
            ("Programmes", "/#programmes"), ("Contact", "/#contact"),
        ]
        for i, (label, url) in enumerate(menu):
            MenuItem.objects.create(label=label, url=url, order=i)
        self.stdout.write("OK Menu")

        HeroSlide.objects.all().delete()
        slides = [
            ("Lycée National François Cappoix de Limonade", "S'instruire pour mieux servir"),
            ("Une éducation d'excellence", "Former les leaders de demain"),
            ("Réussite et discipline", "Ensemble vers la réussite"),
        ]
        for i, (title, subtitle) in enumerate(slides):
            slide = HeroSlide(title=title, subtitle=subtitle, order=i)
            slide.image.save(f"hero-{i + 1}.jpg", gradient_image(1600, 900, PALETTE[i]), save=False)
            slide.save()
        self.stdout.write("OK HeroSlides")

        if not About.objects.exists():
            about = About(
                title="À Propos du Lycée",
                text=(
                    "Le Lycée National François Cappoix de Limonade (LNFCL) est un "
                    "établissement public d'enseignement secondaire situé à Limonade. "
                    "Depuis sa fondation, il forme des générations d'élèves dans un "
                    "cadre de discipline, de savoir et de service à la communauté."
                ),
                stat_students=850, stat_teachers=42, stat_years=75, stat_graduates=5200,
                director_name="Le Directeur",
                director_message=(
                    "Bienvenue au LNFCL. Notre mission est d'offrir à chaque élève "
                    "une formation solide, humaine et citoyenne."
                ),
                mission="Offrir un enseignement secondaire de qualité, accessible et équitable.",
                vision="Devenir un lycée de référence académique et citoyenne en Haïti.",
                values="Discipline, respect, excellence, solidarité.",
            )
            about.image.save("about.jpg", gradient_image(900, 700, PALETTE[0]), save=False)
            about.director_photo.save("directeur.jpg", gradient_image(400, 400, PALETTE[3]), save=False)
            about.save()
        self.stdout.write("OK About")

        Service.objects.all().delete()
        services = [
            ("Enseignement Secondaire", "Cours classique du fondamental au secondaire, avec des professeurs qualifiés.", "bi-mortarboard"),
            ("Bibliothèque", "Un espace de lecture et de recherche pour tous les élèves.", "bi-book"),
            ("Laboratoire", "Travaux pratiques en sciences pour renforcer l'apprentissage.", "bi-flask"),
            ("Encadrement & Orientation", "Suivi personnalisé et orientation scolaire des élèves.", "bi-people-fill"),
            ("Activités Culturelles", "Théâtre, débat, musique et clubs étudiants.", "bi-palette"),
            ("Activités Sportives", "Football, basket-ball et autres disciplines.", "bi-trophy"),
        ]
        for i, (title, desc, icon) in enumerate(services):
            Service.objects.create(title=title, description=desc, icon=icon, order=i)
        self.stdout.write("OK Services")

        Program.objects.all().delete()
        programs = [
            ("Cycle Fondamental", "De la 1ère à la 9ème année fondamentale : bases solides en lecture, écriture et calcul.", "Fondamental"),
            ("Cycle Secondaire", "Seconde, Rhéto et Philo : préparation aux examens d'État.", "Secondaire"),
            ("Nouveau Secondaire", "Réforme du secondaire avec une approche par compétences.", "Nouveau Secondaire"),
        ]
        for i, (name, desc, level) in enumerate(programs):
            program = Program(name=name, description=desc, level=level, order=i)
            program.image.save(f"programme-{i + 1}.jpg", gradient_image(800, 500, PALETTE[i + 1]), save=False)
            program.save()
        self.stdout.write("OK Programmes")

        GalleryImage.objects.all().delete()
        categories = ["Événement", "Classe", "Sport", "Culture"]
        for i in range(8):
            image = GalleryImage(
                title=f"Photo {i + 1}", category=random.choice(categories), order=i
            )
            image.image.save(
                f"galerie-{i + 1}.jpg",
                gradient_image(700, 500, random.choice(PALETTE)),
                save=False,
            )
            image.save()
        self.stdout.write("OK Galerie")

        NewsEvent.objects.all().delete()
        news = [
            ("Rentrée scolaire 2026-2027", "La rentrée officielle aura lieu le lundi 7 septembre. Tous les élèves doivent être en uniforme."),
            ("Résultats des examens d'État", "Félicitations à nos candidats de Rhéto et Philo pour un taux de réussite remarquable."),
            ("Journée culturelle annuelle", "Expositions, chansons et théâtre présentés par les élèves de toutes les classes."),
        ]
        for i, (title, body) in enumerate(news):
            item = NewsEvent(title=title, body=body, is_published=True)
            item.image.save(f"news-{i + 1}.jpg", gradient_image(800, 450, PALETTE[i % len(PALETTE)]), save=False)
            item.save()
        self.stdout.write("OK Nouvelles")

        TeamMember.objects.all().delete()
        team = [
            ("M. Jean Baptiste", "Directeur", "Administration"),
            ("Mme Marie Claire", "Professeure de Lettres", "Français, Créole"),
            ("M. Pierre Louis", "Professeur de Mathématiques", "Algèbre, Géométrie"),
            ("Mme Suzette Dorsainvil", "Professeure de Sciences", "Biologie, Chimie"),
        ]
        for i, (name, position, subjects) in enumerate(team):
            member = TeamMember(name=name, position=position, subjects=subjects, order=i)
            member.photo.save(f"membre-{i + 1}.jpg", gradient_image(400, 400, PALETTE[i % len(PALETTE)]), save=False)
            member.save()
        self.stdout.write("OK Équipe")

        Result.objects.all().delete()
        results = [
            ("Résultats examens d'État - Philo", "2025-2026", True),
            ("Résultats examens d'État - Rhéto", "2025-2026", True),
            ("Résultats internes - 9ème AF", "2025-2026", False),
        ]
        for i, (title, year, is_public) in enumerate(results):
            result = Result(title=title, school_year=year, is_public=is_public)
            result.pdf_file.save(f"resultats-{i + 1}.pdf", minimal_pdf(title), save=False)
            result.save()
        self.stdout.write("OK Résultats")


        Testimonial.objects.all().delete()
        testimonials = [
            ("Nathalie Jean", "3ème AF", "Nan lekòl sa, mwen dekouvri pasyon mwen pou syans. Pwofesè yo toujou gen tan pou ede w jis ou konprann."),
            ("Widley Pierre", "Seconde", "Klib deba a chanje lavi mwen — kounye a mwen pale devan tout moun san krentifaj."),
            ("Madame Laguerre", "Paran", "Depi timoun mwen an antre nan lekòl sa, rezilta li e konfyans li anpil pi wo."),
        ]
        for i, (name, klass, quote) in enumerate(testimonials):
            t = Testimonial(name=name, class_name=klass, quote=quote, order=i)
            t.photo.save(
                f"temwayaj-{i + 1}.jpg",
                gradient_image(300, 300, PALETTE[i % len(PALETTE)]),
                save=False,
            )
            t.save()
        self.stdout.write("OK Témwayaj")

        Club.objects.all().delete()
        clubs = [
            ("Klib Débat & Éloquence", "KLUB", "Aprann pale devan moun, defann yon pozisyon ak sipase la pèl ak lòt elèv.", "Mèkredi 14h – 16h"),
            ("Espò — Bol (Foutbol)", "ESPO", "Ekip gason ak fi, antrènman anyèl ak match amikal ak lòt lekòl yo.", "Madi ak Jedi 16h – 17h30"),
            ("Klib Syans & Robotik", "AKTIVITE", "Eksperimantasyon, robotik, kodaj ak sèvi ak enfòmatik.", "Vanredi 13h – 15h"),
        ]
        for i, (name, category, description, schedule) in enumerate(clubs):
            c = Club(name=name, category=category, description=description, schedule=schedule, order=i)
            c.image.save(
                f"klib-{i + 1}.jpg",
                gradient_image(700, 450, PALETTE[i % len(PALETTE)]),
                save=False,
            )
            c.save()
        self.stdout.write("OK Klib")

        SchoolEvent.objects.all().delete()
        today = timezone.localdate()
        SchoolEvent.objects.create(
            title="Rentrée scolaire",
            description="Premye joulekòl la — tout elèv davè.",
            location="Kou LNFCL",
            date=today + timedelta(days=12),
        )
        SchoolEvent.objects.create(
            title="Réunion Parents-Professeurs",
            description="Twouman rezilta twouzyèm péryèd la.",
            location="Salle polyvalente",
            date=today + timedelta(days=20),
        )
        SchoolEvent.objects.create(
            title="Journée Culturelle",
            description="Ekzibisyon, dans, teyat ak chante elèv yo!",
            location="Cour d'honneur",
            date=today + timedelta(days=35),
            end_date=today + timedelta(days=37),
        )
        self.stdout.write("OK Kalandriye")

        FAQ.objects.all().delete()
        faqs = [
            ("Ki lè enskripsyon an kòmanse?", "Pre-enskripsyon an ap fèt an liy tout ane a. Lekòl la ap kontakte ou nan anpil kout jan demann lan soumèt."),
            ("Ki dokiman ki obligatwa?", "Se sèlman non, seks, dat nesans ak telefòn ki obligatwa. Ake nesans ak bilten se opsyonèl — ou ka pore yo pita."),
            ("Èsk mwen ka enskri yon elèv ki pa te nan lekòl la?", "Wi! Jis klike sou « Pré-inscription » anwo paj la. Rantre nan 4 etap yo epi resevwa yon nimewo referans PRE-XXXXXXXX."),
            ("Ki nivo ki disponib?", "Préscolaire, 1ère – 6ème AF (primaire), 7ème – 9ème AF ak Secondaire (NS1 – NS4)."),
        ]
        for i, (q, a) in enumerate(faqs):
            FAQ.objects.create(question=q, answer=a, order=i)
        self.stdout.write("OK FAQ")

        self.stdout.write(self.style.SUCCESS("Contenu de démonstration créé avec succès."))
