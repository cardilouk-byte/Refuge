from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

from .models import ContactMessage, Result, SiteSettings


class HomeViewTests(TestCase):
    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LNFCL")

    def test_home_contains_menu_and_motto(self):
        from .models import MenuItem

        SiteSettings.load()
        MenuItem.objects.create(label="Accueil", url="/#accueil", order=0)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Accueil")
        self.assertContains(response, "instruire pour mieux servir")

    def test_contact_form_saves_message(self):
        response = self.client.post(
            reverse("home"),
            {
                "name": "Jean Test",
                "email": "jean@example.com",
                "subject": "Renseignements",
                "message": "Bonjour, je voudrais des informations.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertContains(response, "envoyé avec succès")

    def test_contact_form_invalid_does_not_save(self):
        self.client.post(reverse("home"), {"name": "", "email": "pas-un-email"})
        self.assertEqual(ContactMessage.objects.count(), 0)


class ResultsViewTests(TestCase):
    def setUp(self):
        Result.objects.create(
            title="Public", school_year="2025-2026", is_public=True,
            pdf_file="resultats/public.pdf",
        )
        Result.objects.create(
            title="Prive", school_year="2025-2026", is_public=False,
            pdf_file="resultats/prive.pdf",
        )

    def test_anonymous_sees_only_public_results(self):
        response = self.client.get(reverse("results"))
        self.assertContains(response, "Public")
        self.assertNotContains(response, "Prive")

    def test_authenticated_sees_all_results(self):
        User.objects.create_user("user1", password="pass12345")
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("results"))
        self.assertContains(response, "Public")
        self.assertContains(response, "Prive")


class AuthTests(TestCase):
    def test_login_page_returns_200(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_login_and_logout(self):
        User.objects.create_user("user1", password="pass12345")
        response = self.client.post(
            reverse("login"), {"username": "user1", "password": "pass12345"}, follow=True
        )
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, "Déconnexion")
        self.client.post(reverse("logout"))
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Connecter")


    def test_logout_with_post(self):
        user = User.objects.create_user("logoutuser", password="pass12345")
        self.client.force_login(user)
        response = self.client.post("/deconnexion/")
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

class SignupTests(TestCase):
    def test_signup_page_returns_200(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inscription")

    def test_signup_creates_account_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "nouvo", "password1": "ModpasFò2026!", "password2": "ModpasFò2026!"},
            follow=True,
        )
        self.assertTrue(User.objects.filter(username="nouvo").exists())
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertContains(response, "compte a été créé")

    def test_signup_weak_password_rejected(self):
        self.client.post(
            reverse("signup"),
            {"username": "fob", "password1": "123", "password2": "123"},
        )
        self.assertFalse(User.objects.filter(username="fob").exists())

    def test_authenticated_user_redirected_from_signup(self):
        User.objects.create_user("user1", password="pass12345")
        self.client.login(username="user1", password="pass12345")
        response = self.client.get(reverse("signup"))
        self.assertRedirects(response, reverse("home"))


class HwInspiredPagesTests(TestCase):
    """Paj piblik nèf enpsire pa konsepsyon hw.com."""

    @classmethod
    def setUpTestData(cls):
        from datetime import time
        from datetime import date as date_cls

        from .models import Club, FAQ, MenuItem, SchoolEvent, Testimonial

        cls.parent_item = MenuItem.objects.create(label="Lekòl la", url="/apropo/", order=1)
        cls.child_item = MenuItem.objects.create(label="Istwa", url="/apropo/", parent=cls.parent_item, order=1)
        cls.hidden_child = MenuItem.objects.create(label="Ki pa vizib", url="/apropo/", parent=cls.parent_item, is_visible=False, order=2)
        Testimonial.objects.create(name="Nathalie Jean", class_name="3ème AF", quote="Lekòl sa a chanje lavi mwen.")
        Club.objects.create(name="Klib Débat", category="KLUB", description="Aprann pale devan moun.")
        cls.event = SchoolEvent.objects.create(
            title="Journée Culturelle",
            date=date_cls(2099, 5, 8),
            location="Cour d'honneur",
        )
        FAQ.objects.create(question="Ki lè enskripsyon an kòmanse?", answer="Toulepremye setanm.")

    def test_new_pages_return_200(self):
        for url_name in ["calendar", "school_life", "faq", "how_to_apply", "about_page"]:
            response = self.client.get(reverse(url_name), HTTP_HOST="localhost")
            self.assertEqual(response.status_code, 200, url_name)

    def test_calendar_shows_event_in_grid(self):
        response = self.client.get(reverse("calendar") + "?m=2099-05", HTTP_HOST="localhost")
        self.assertContains(response, "Journée Culturelle")
        self.assertContains(response, "cal-event")

    def test_faq_shows_published_questions(self):
        response = self.client.get(reverse("faq"), HTTP_HOST="localhost")
        self.assertContains(response, "Ki lè enskripsyon an kòmanse?")

    def test_apply_page_shows_steps_and_cta(self):
        response = self.client.get(reverse("how_to_apply"), HTTP_HOST="localhost")
        self.assertContains(response, "Etap enskripsyon yo")
        self.assertContains(response, "/preinscription/")

    def test_mega_menu_renders_children_without_duplication(self):
        html = self.client.get(reverse("home"), HTTP_HOST="localhost").content.decode()
        self.assertIn("dropdown-toggle", html)
        self.assertIn("Istwa", html)
        self.assertNotIn("Ki pa vizib", html)
        self.assertEqual(html.count(">Lekòl la<"), 1)

    def test_home_sections_respect_toggles(self):
        settings_obj = SiteSettings.load()
        response = self.client.get(reverse("home"), HTTP_HOST="localhost")
        self.assertContains(response, "lavi-lekol")
        self.assertContains(response, "testimonialCarousel")
        settings_obj.show_school_life = False
        settings_obj.show_testimonials = False
        settings_obj.save()
        html = self.client.get(reverse("home"), HTTP_HOST="localhost").content.decode()
        self.assertNotIn('id="lavi-lekol"', html)
        self.assertNotIn("testimonialCarousel", html)

    def test_about_page_shows_stats_and_clubs(self):
        response = self.client.get(reverse("about_page"), HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)

    def test_life_page_shows_club_grouped(self):
        response = self.client.get(reverse("school_life"), HTTP_HOST="localhost")
        self.assertContains(response, "Klib Débat")
        self.assertContains(response, "Klib")


class ButtonColorTests(TestCase):
    """Tout bouton mark yo dwe swiv koulè prensipal la nan Configuration."""

    def _html(self):
        return self.client.get(reverse("home"), HTTP_HOST="localhost").content.decode()

    def test_buttons_follow_primary_color(self):
        from .models import SiteSettings
        settings_obj = SiteSettings.load()
        settings_obj.primary_color = "#e91e63"
        settings_obj.save()
        html = self._html()
        self.assertIn("--primary: #e91e63", html)
        self.assertIn("233, 30, 99", html)
        self.assertIn("--bs-btn-bg: var(--primary)", html)

    def test_button_override_present_on_portal(self):
        from accounts.models import User as U
        from students.models import Student
        u, _ = U.objects.get_or_create(username="btn_elv", defaults={"role": "ELEVE"})
        u.set_password("T43s!pass")
        u.save()
        Student.objects.get_or_create(user=u, defaults={"matricule": "ELV-77777", "first_name": "Btn", "last_name": "Elèv"})
        c = self.client
        c.login(username="btn_elv", password="T43s!pass")
        response = c.get("/portail/eleve/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("--bs-btn-bg: var(--primary)", html)
        self.assertNotIn("--primary: #0d6efd; }", html)


class FullDesignColorTests(TestCase):
    """Tout palet sit la (premye, sikonndè, siksè, danje, avètisman, info) dwe configurable epi swiv tout kote."""

    def _settings(self, **kwargs):
        from .models import SiteSettings
        obj = SiteSettings.load()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.save()
        return obj

    def test_root_vars_inject_all_brands(self):
        obj = self._settings(secondary_color="#111111", success_color="#222222",
                             info_color="#333333", warning_color="#444444", danger_color="#555555")
        html = self.client.get(reverse("home"), HTTP_HOST="localhost").content.decode()
        self.assertIn("--secondary-color: #111111", html)
        self.assertIn("--success-color: #222222", html)
        self.assertIn("--info-color: #333333", html)
        self.assertIn("--warning-color: #444444", html)
        self.assertIn("--danger-color: #555555", html)

    def test_semantic_button_overrides_render(self):
        html = self.client.get(reverse("home"), HTTP_HOST="localhost").content.decode()
        for sel in [".btn-primary {", ".btn-outline-primary {", ".btn-success {", ".btn-danger {",
                    ".btn-warning {", ".btn-info {", ".btn-secondary {", ".bg-danger",
                    ".text-success", ".alert-danger"]:
            self.assertIn(sel, html)

    def test_portal_gets_full_palette(self):
        from accounts.models import User as U
        from students.models import Student
        u, _ = U.objects.get_or_create(username="design_elv", defaults={"role": "ELEVE"})
        u.set_password("T43s!pass")
        u.save()
        Student.objects.get_or_create(user=u, defaults={"matricule": "ELV-88888", "first_name": "D", "last_name": "E"})
        c = self.client
        c.login(username="design_elv", password="T43s!pass")
        response = c.get("/portail/eleve/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("--danger-color", html)
        self.assertIn(".btn-success {", html)

    def test_settings_form_has_color_fields(self):
        from accounts.models import User as U
        u, _ = U.objects.get_or_create(username="design_su", defaults={"role": "SUPERADMIN", "is_staff": True, "is_superuser": True})
        u.set_password("T43s!pass")
        u.save()
        c = self.client
        c.login(username="design_su", password="T43s!pass")
        response = c.get("/configuration/parametres/", HTTP_HOST="localhost")
        html = response.content.decode()
        for name in ["success_color", "danger_color", "warning_color", "info_color", "secondary_color"]:
            self.assertIn(f'name="{name}"', html)


class DashboardLogoTests(TestCase):
    """Logo institution an ap parèt nan dashboard + pòtay yo."""

    def test_portal_shows_logo_when_uploaded(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from io import BytesIO
        from PIL import Image
        from .models import SiteSettings
        from accounts.models import User
        buf = BytesIO()
        Image.new("RGB", (120, 120), (13, 110, 253)).save(buf, "PNG")
        settings_obj = SiteSettings.load()
        settings_obj.logo.save("logo-t.png", SimpleUploadedFile("logo-t.png", buf.getvalue(), "image/png"), save=True)
        u, _ = User.objects.get_or_create(username="logo_elv", defaults={"role": "ELEVE"})
        u.set_password("T43s!pass")
        u.save()
        c = self.client
        c.login(username="logo_elv", password="T43s!pass")
        response = c.get("/portail/eleve/", HTTP_HOST="localhost")
        html = response.content.decode()
        self.assertIn("/media/site/logo-t", html)
        self.assertIn("portal-logo", html)

    def test_portal_shows_placeholder_without_logo(self):
        from .models import SiteSettings
        from accounts.models import User
        settings_obj = SiteSettings.load()
        settings_obj.logo = None
        settings_obj.save()
        u, _ = User.objects.get_or_create(username="logo_elv2", defaults={"role": "ELEVE"})
        u.set_password("T43s!pass")
        u.save()
        c = self.client
        c.login(username="logo_elv2", password="T43s!pass")
        response = c.get("/portail/eleve/", HTTP_HOST="localhost")
        html = response.content.decode()
        self.assertIn('class="brand-logo-placeholder"', html)
        self.assertNotIn('class="portal-logo"', html)



class SidebarSectionsTest(TestCase):
    def _login(self, username, role):
        from accounts.models import User
        user, _ = User.objects.get_or_create(username=username, defaults={"role": role})
        user.set_password("T43s!pass")
        user.save()
        self.client.login(username=username, password="T43s!pass")
        return user

    def test_teacher_sees_etablissement_section_with_students(self):
        self._login("sb_prof", "ENSEIGNANT")
        html = self.client.get("/eleve/", HTTP_HOST="localhost").content.decode()
        self.assertEqual(self.client.get("/eleve/", HTTP_HOST="localhost").status_code, 200)
        self.assertIn("ÉTABLISSEMENT", html)
        self.assertIn("Elèv yo", html)
        self.assertIn(">Devoirs<", html)
        self.assertIn(">Examens<", html)
        self.assertIn("KLAS &amp; KOUR", html)

    def test_student_sees_own_sidebar_without_staff_sections(self):
        self._login("sb_elv", "ELEVE")
        html = self.client.get("/portail/eleve/", HTTP_HOST="localhost").content.decode()
        self.assertIn("EKÒL MWEN", html)
        self.assertIn("Bulletin mwen", html)
        self.assertIn("Kat idantite mwen", html)
        self.assertNotIn("ÉTABLISSEMENT", html)
        self.assertNotIn(">Tableau de bord<", html)

    def test_direction_sidebar_full_sections(self):
        from accounts.models import User
        user, _ = User.objects.get_or_create(username="sb_dir", defaults={"role": "DIRECTION"})
        user.set_password("T43s!pass")
        user.save()
        self.client.login(username="sb_dir", password="T43s!pass")
        html = self.client.get("/tableau/", HTTP_HOST="localhost").content.decode()
        self.assertIn("ÉTABLISSEMENT", html)
        self.assertIn("Nouvèl ane", html)
        self.assertIn("Backup", html)
        self.assertIn("Elèv yo", html)
