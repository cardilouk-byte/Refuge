from io import BytesIO

from django.contrib.auth import get_user_model
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from core.models import HeroSlide, SiteSettings

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
