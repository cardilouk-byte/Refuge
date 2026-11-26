from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from students.models import Parent, ParentStudent, Student

User = get_user_model()


class RoleRedirectTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True
        )
        User.objects.create_user(username="prof1", password="test1234!", role=User.Role.ENSEIGNANT)
        User.objects.create_user(username="parent1", password="test1234!", role=User.Role.PARENT)

    def test_role_home_redirects_staff_to_dashboard(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("accounts:role_home"))
        self.assertRedirects(response, reverse("dashboard:home"), fetch_redirect_response=False)

    def test_role_home_redirects_teacher_to_portal(self):
        self.client.login(username="prof1", password="test1234!")
        response = self.client.get(reverse("accounts:role_home"))
        self.assertRedirects(response, reverse("portals:professeur"), fetch_redirect_response=False)

    def test_role_home_requires_login(self):
        response = self.client.get(reverse("accounts:role_home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("connexion", response.url)


class DashboardAccessTest(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="dir1", password="test1234!", role=User.Role.DIRECTION, is_staff=True
        )
        User.objects.create_user(username="parent1", password="test1234!", role=User.Role.PARENT)

    def test_dashboard_accessible_to_staff(self):
        self.client.login(username="dir1", password="test1234!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord")

    def test_dashboard_denied_to_parent(self):
        self.client.login(username="parent1", password="test1234!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)


class PortalAccessTest(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(username="eleve1", password="test1234!", role=User.Role.ELEVE)
        self.parent_user = User.objects.create_user(username="parent1", password="test1234!", role=User.Role.PARENT)
        self.student = Student.objects.create(
            matricule="ELV-TEST-001", first_name="Test", last_name="Élève", user=self.student_user
        )
        self.parent = Parent.objects.create(first_name="Test", last_name="Parent", user=self.parent_user)
        ParentStudent.objects.create(parent=self.parent, student=self.student)

    def test_professeur_portal(self):
        User.objects.create_user(username="prof1", password="test1234!", role=User.Role.ENSEIGNANT)
        self.client.login(username="prof1", password="test1234!")
        response = self.client.get(reverse("portals:professeur"))
        self.assertEqual(response.status_code, 200)

    def test_eleve_portal_shows_student(self):
        self.client.login(username="eleve1", password="test1234!")
        response = self.client.get(reverse("portals:eleve"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Élève")

    def test_parent_portal_lists_children(self):
        self.client.login(username="parent1", password="test1234!")
        response = self.client.get(reverse("portals:parent"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Élève")

    def test_parent_cannot_see_other_children(self):
        other = Student.objects.create(matricule="ELV-TEST-002", first_name="Autre", last_name="Élève")
        self.client.login(username="parent1", password="test1234!")
        response = self.client.get(reverse("portals:child_detail", args=[other.pk]))
        self.assertRedirects(response, reverse("portals:parent"))

    def test_eleve_cannot_access_professeur_portal(self):
        self.client.login(username="eleve1", password="test1234!")
        response = self.client.get(reverse("portals:professeur"))
        self.assertEqual(response.status_code, 403)
