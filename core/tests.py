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
