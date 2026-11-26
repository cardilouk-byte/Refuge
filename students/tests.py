from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from academics.models import ClassRoom, ClassSubject, Cycle, Level, SchoolYear, Subject
from students.models import Student
from teachers.models import Teacher

from .models import Student

User = get_user_model()
HOST = {"HTTP_HOST": "localhost"}


class StudentPortalTest(TestCase):
    def setUp(self):
        year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="2e Sik", order=2)
        level = Level.objects.create(name="7e AF", cycle=cycle, order=7)
        self.classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
        subject = Subject.objects.create(name="Matematik")
        self.prof_user = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        teacher = Teacher.objects.create(matricule="P1", first_name="Jean", last_name="Baptiste", user=self.prof_user)
        self.cs = ClassSubject.objects.create(classroom=self.classroom, subject=subject, teacher=teacher)
        self.dir_user = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)
        self.eleve_user = User.objects.create_user("elv1", password="Pass1234!", role="ELEVE")
        self.student = Student.objects.create(
            matricule="ELV-00001", first_name="Jean", last_name="Test",
            classroom=self.classroom, user=self.eleve_user,
        )

    def test_direction_can_create_student(self):
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post(
            "/eleve/nouveau/",
            {"matricule": "ELV-00002", "first_name": "Marie", "last_name": "Clerger",
             "classroom": self.classroom.pk},
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Student.objects.filter(matricule="ELV-00002").exists())

    def test_eleve_cannot_use_student_crud(self):
        self.client.login(username="elv1", password="Pass1234!")
        self.assertEqual(self.client.get("/eleve/", **HOST).status_code, 403)
        self.assertEqual(self.client.get("/eleve/nouveau/", **HOST).status_code, 403)

    def test_account_creation_gives_credentials(self):
        fresh = Student.objects.create(
            matricule="ELV-00003", first_name="Paul", last_name="Nouvo", classroom=self.classroom
        )
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post(f"/eleve/{fresh.pk}/kont/", {"action": "create"}, **HOST)
        self.assertEqual(response.status_code, 302)
        fresh.refresh_from_db()
        self.assertIsNotNone(fresh.user)
        self.assertEqual(fresh.user.role, "ELEVE")
        response = self.client.get(f"/eleve/{fresh.pk}/kont/", **HOST)
        self.assertContains(response, fresh.user.get_username())
        self.assertContains(response, "Modpas")

    def test_reset_password_creates_new_credentials(self):
        self.client.login(username="dir", password="Pass1234!")
        self.client.post(f"/eleve/{self.student.pk}/kont/", {"action": "reset"}, **HOST)
        self.student.refresh_from_db()
        self.assertIsNotNone(self.student.user)
        pw = self.client.session["student_credentials"]["password"]
        self.assertGreater(len(pw), 0)
        # modpas nèf la mache
        client2 = Client()
        self.assertTrue(
            client2.login(
                username=self.student.user.get_username(),
                password=self.client.session["student_credentials"]["password"],
            )
        )

    def test_admin_gate_superadmin_only(self):
        # DIRECTION gen is_staff men DWE pa gen aks\u00e8 nan admin Django
        no_django_admin = django_admin.site.has_permission(
            type("R", (), {"user": self.dir_user})()
        )
        self.assertFalse(no_django_admin)
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        adm = User.objects.get(username="adm")
        self.assertTrue(django_admin.site.has_permission(type("R", (), {"user": adm})()))

    def test_direction_can_open_admin_page_and_get_403(self):
        self.client.login(username="dir", password="Pass1234!")
        from django.conf import settings

        response = self.client.get(f"/{settings.ADMIN_URL}", **HOST)
        self.assertIn(response.status_code, (403, 302))
        self.assertFalse(response.wsgi_request.user.is_superuser)
