from io import BytesIO

from django.contrib.auth import get_user_model
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from core.models import GalleryImage, HeroSlide, SiteSettings

User = get_user_model()


def _png(name="test.png"):
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def _mp4(name="test.mp4"):
    return SimpleUploadedFile(name, b"fake-video-content", content_type="video/mp4")


class ConfigAccessTest(TestCase):
    def test_anonymous_redirects_to_login(self):
        response = self.client.get("/configuration/")
        self.assertEqual(response.status_code, 302)

    def test_staff_non_superuser_gets_403(self):
        User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/configuration/")
        self.assertEqual(response.status_code, 403)

    def test_superuser_gets_200(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")
        for url in ["/configuration/", "/configuration/parametres/", "/configuration/slides/", "/configuration/meni/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_section_redirects(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get("/configuration/pa-egziste/")
        self.assertEqual(response.status_code, 302)


class ConfigCrudTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")

    def test_create_slide(self):
        response = self.client.post(
            "/configuration/slides/nouveau/",
            {"title": "Slide Test", "subtitle": "", "button_text": "Lire Plus", "button_url": "/#apropos", "order": 0, "is_active": "on"},
        )
        self.assertRedirects(response, "/configuration/slides/")
        self.assertTrue(HeroSlide.objects.filter(title="Slide Test").exists())

    def test_update_slide(self):
        slide = HeroSlide.objects.create(title="Avan")
        response = self.client.post(
            f"/configuration/slides/{slide.pk}/",
            {"title": "Apre", "subtitle": "", "button_text": "Lire Plus", "button_url": "/#apropos", "order": 0, "is_active": "on"},
        )
        self.assertRedirects(response, "/configuration/slides/")
        slide.refresh_from_db()
        self.assertEqual(slide.title, "Apre")

    def test_delete_slide(self):
        slide = HeroSlide.objects.create(title="Efase m")
        response = self.client.post(f"/configuration/slides/{slide.pk}/supprimer/")
        self.assertRedirects(response, "/configuration/slides/")
        self.assertFalse(HeroSlide.objects.filter(pk=slide.pk).exists())

    def test_apropos_single_object(self):
        response = self.client.get("/configuration/apropos/")
        self.assertRedirects(response, "/configuration/apropos/1/")


class SiteSettingsConfigTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")
        self.settings_obj = SiteSettings.load()

    def _payload(self, **extra):
        from dashboard.config_forms import SiteSettingsForm
        form = SiteSettingsForm(instance=self.settings_obj)
        data = {}
        for name, field in form.fields.items():
            if isinstance(field, forms.FileField):
                continue
            value = getattr(self.settings_obj, name)
            if isinstance(field, forms.BooleanField):
                if value:
                    data[name] = "on"
            else:
                data[name] = str(value)
        if not data.get("name"):
            data["name"] = "LNFCL"
        data.update(extra)
        return data

    def test_change_primary_color(self):
        response = self.client.post("/configuration/parametres/", self._payload(primary_color="#ff0000"))
        self.assertRedirects(response, "/configuration/parametres/")
        self.assertEqual(SiteSettings.load().primary_color, "#ff0000")
        home = self.client.get("/", HTTP_HOST="localhost")
        self.assertIn("--primary: #ff0000", home.content.decode())

    def test_marquee_shows_when_enabled(self):
        self.client.post(
            "/configuration/parametres/",
            self._payload(marquee_enabled="on", marquee_text="Inskripsyon louvri!"),
        )
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("marquee-bar", home)
        self.assertIn("Inskripsyon louvri!", home)

    def test_marquee_hidden_when_disabled(self):
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertNotIn("marquee-bar", home)

    def test_section_hidden_when_disabled(self):
        self.client.post("/configuration/parametres/", self._payload(show_services="", show_gallery=""))
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertNotIn('id="services"', home)
        self.assertNotIn('id="galerie"', home)
        self.assertIn('id="apropos"', home)

    def test_hero_video_renders(self):
        HeroSlide.objects.create(title="Slide Video", video=_mp4())
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("hero-video", home)

    def test_gallery_video_renders(self):
        from core.models import GalleryImage
        GalleryImage.objects.create(title="Video Galri", video=_mp4())
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("<video", home)


class AnimationSettingsTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")
        self.settings_obj = SiteSettings.load()

    def _payload(self, **extra):
        from dashboard.config_forms import SiteSettingsForm
        form = SiteSettingsForm(instance=self.settings_obj)
        data = {}
        for name, field in form.fields.items():
            if isinstance(field, forms.FileField):
                continue
            value = getattr(self.settings_obj, name)
            if isinstance(field, forms.BooleanField):
                if value:
                    data[name] = "on"
            else:
                data[name] = str(value)
        if not data.get("name"):
            data["name"] = "LNFCL"
        data.update(extra)
        return data

    def test_slider_effect_rendered(self):
        self.client.post("/configuration/parametres/", self._payload(slider_effect="zoom"))
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("effect-zoom", home)

    def test_section_animation_rendered(self):
        self.client.post("/configuration/parametres/", self._payload(section_animation="flip-left"))
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn('data-aos="flip-left"', home)

    def test_hero_text_position(self):
        self.client.post("/configuration/parametres/", self._payload(hero_text_position="center"))
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("hero-text-center", home)

    def test_hero_hidden_when_disabled(self):
        self.client.post("/configuration/parametres/", self._payload(show_hero=""))
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertNotIn('id="accueil"', home)


class MediaServingTest(TestCase):
    def test_media_served_even_when_debug_false(self):
        from core.models import GalleryImage
        with override_settings(DEBUG=False):
            item = GalleryImage.objects.create(title="Foto", image=_png("foto.png"))
            response = self.client.get(item.image.url)
            self.assertEqual(response.status_code, 200)

    def test_large_image_compressed_on_save(self):
        from io import BytesIO
        from PIL import Image
        from core.models import GalleryImage
        from django.core.files.uploadedfile import SimpleUploadedFile as S
        buffer = BytesIO()
        Image.new("RGB", (3000, 2000), "red").save(buffer, format="JPEG", quality=95)
        big = S("gwo.jpg", buffer.getvalue(), content_type="image/jpeg")
        item = GalleryImage.objects.create(title="Gwo foto", image=big)
        img = Image.open(item.image)
        self.assertLessEqual(max(img.size), 1600)

    def test_mov_video_accepted(self):
        from django.core.exceptions import ValidationError
        from core.models import HeroSlide
        slide = HeroSlide(title="Video mov", video=_mp4("klip.mov"))
        slide.full_clean(exclude=["image"])


class DetailModalTest(TestCase):
    def setUp(self):
        SiteSettings.load()

    def test_team_modal_renders_with_details(self):
        from core.models import TeamMember
        TeamMember.objects.create(
            name="Jean Pierre", position="Pwofesè Matematik",
            subjects="Aljèb, Jeyometri", email="jean@lnfcl.edu.ht",
            bio="Yon pwofesè ki gen 10 ane eksperyans.",
        )
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("teamModal1", home)
        self.assertIn("jean@lnfcl.edu.ht", home)
        self.assertIn("10 ane eksperyans", home)
        self.assertIn('data-bs-toggle="modal"', home)

    def test_program_modal_renders_with_details(self):
        from core.models import Program
        Program.objects.create(
            name="Syans Eksperimantal", level="Secondaire",
            description="Pwogram syans konplè ak laboratwa.",
        )
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("programModal1", home)
        self.assertIn("Pwogram syans konplè ak laboratwa.", home)
        self.assertIn("Gade plis detay", home)

    def test_map_embed_from_address(self):
        settings_obj = SiteSettings.load()
        settings_obj.address = "Limonade, Cap-Haïtien, Haïti"
        settings_obj.google_maps_url = ""
        settings_obj.save()
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("https://www.google.com/maps?q=", home)
        self.assertIn("output=embed", home)

    def test_map_prefers_google_maps_url(self):
        settings_obj = SiteSettings.load()
        settings_obj.address = "Limonade, Haïti"
        settings_obj.google_maps_url = "https://maps.google.com/embed?pb=test"
        settings_obj.save()
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("https://maps.google.com/embed?pb=test", home)
        self.assertNotIn("https://www.google.com/maps?q=", home)


class OptionalFieldsTest(TestCase):
    def setUp(self):
        SiteSettings.load()
        User.objects.create_superuser("admin", "admin@lnfcl.edu.ht", "AdminLNFCL2026!")
        self.client.login(username="admin", password="AdminLNFCL2026!")

    def test_gallery_saves_without_optional_fields(self):
        response = self.client.post(
            "/configuration/galri/nouveau/",
            {"title": "Foto San Orè", "image": _png("foto.png")},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        item = GalleryImage.objects.get(title="Foto San Orè")
        self.assertEqual(item.order, 0)
        self.assertEqual(item.category, "Général")

    def test_gallery_image_appears_on_home(self):
        self.client.post(
            "/configuration/galri/nouveau/",
            {"title": "Foto Vitrine", "image": _png("foto.png")},
            follow=True,
        )
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        self.assertIn("galerie/foto", home)

    def test_slide_saves_active_with_default_button(self):
        self.client.post("/configuration/slides/nouveau/", {"title": "Slide Fasil", "is_active": "on"}, follow=True)
        slide = HeroSlide.objects.get(title="Slide Fasil")
        self.assertTrue(slide.is_active)
        self.assertEqual(slide.button_text, "Lire Plus")
        self.assertEqual(slide.button_url, "/#apropos")

    def test_active_checkbox_checked_by_default(self):
        response = self.client.get("/configuration/slides/nouveau/")
        self.assertIn("checked", response.content.decode())


class HeroOverlayTest(TestCase):
    def setUp(self):
        SiteSettings.load()

    def test_no_overlay_when_slide_has_image(self):
        slide = HeroSlide(title="Ak Imaj", order=99)
        slide.image.save("overlay-test.jpg", _png("overlay-test.jpg"), save=True)
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        block = home[home.find("Ak Imaj") - 800:home.find("Ak Imaj")]
        self.assertIn("background-image", block)
        self.assertNotIn("hero-overlay", block)

    def test_overlay_kept_when_slide_has_no_image(self):
        HeroSlide.objects.create(title="San Imaj", order=99)
        home = self.client.get("/", HTTP_HOST="localhost").content.decode()
        block = home[home.find("San Imaj") - 800:home.find("San Imaj")]
        self.assertNotIn("background-image", block)
        self.assertIn("hero-overlay", block)
