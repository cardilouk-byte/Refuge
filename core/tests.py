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
        self.client.force_login(self.user)
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
