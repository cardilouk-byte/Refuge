from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from academics.models import Cycle, Level
from students.models import Parent, ParentStudent, Student

from .models import PreRegistration

User = get_user_model()


class PreRegistrationWizardTest(TestCase):
    def _full_flow(self):
        r1 = self.client.post("/preinscription/etap/1/", {
            "first_name": "Marie", "last_name": "Jean", "gender": "F",
            "birth_date": "2012-05-10", "birth_place": "Limonade", "address": "",
        })
        self.assertRedirects(r1, "/preinscription/etap/2/")
        r2 = self.client.post("/preinscription/etap/2/", {
            "parent_name": "Paul Jean", "parent_relation": "PERE", "parent_phone": "+50937000000",
        })
        self.assertRedirects(r2, "/preinscription/etap/3/")
        r3 = self.client.post("/preinscription/etap/3/", {
            "previous_school": "École Nationale", "last_class": "6ème AF", "notes": "",
        })
        self.assertRedirects(r3, "/preinscription/rezime/")
        return self.client.post("/preinscription/rezime/")

    def test_optional_fields_not_required(self):
        response = self._full_flow()
        self.assertContains(response, "PRE-")
        pre = PreRegistration.objects.get(first_name="Marie")
        self.assertEqual(pre.status, "SOUMET")
        self.assertIsNone(pre.desired_level)
        self.assertEqual(pre.previous_school, "École Nationale")

    def test_step_requires_session_data(self):
        response = self.client.get("/preinscription/rezime/")
        self.assertRedirects(response, "/preinscription/", fetch_redirect_response=False)

    def test_wizard_shows_modern_stepper(self):
        response = self.client.get("/preinscription/etap/1/")
        html = response.content.decode()
        self.assertIn("pre-steps", html)
        self.assertIn("El\u00e8v", html)
        self.assertIn("Etap 1 sou 4", html)

    def test_review_page_matches_new_layout(self):
        self.client.post("/preinscription/etap/1/", {
            "first_name": "Marie", "last_name": "Jean", "gender": "F", "birth_date": "2012-05-10",
        })
        self.client.post("/preinscription/etap/2/", {
            "parent_name": "Paul Jean", "parent_relation": "PERE", "parent_phone": "+50937000000",
        })
        self.client.post("/preinscription/etap/3/", {})
        response = self.client.get("/preinscription/rezime/")
        html = response.content.decode()
        self.assertIn("sum-card", html)
        self.assertIn("Marie Jean", html)
        self.assertNotIn("</alert>", html)


class PreRegistrationAdminTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.client.login(username="adm", password="Pass1234!")
        self.pre = PreRegistration.objects.create(
            first_name="Marie", last_name="Jean", gender="F", birth_date=date(2012, 5, 10),
            parent_name="Paul Jean", parent_phone="+50937000000", status="ACCEPTE",
        )

    def test_list_accessible(self):
        self.assertEqual(self.client.get("/preinscriptions/").status_code, 200)

    def test_anonymous_cannot_see_admin_list(self):
        client = self.client_class()
        response = client.get("/preinscriptions/")
        self.assertEqual(response.status_code, 302)

    def test_set_status(self):
        response = self.client.post(f"/preinscriptions/{self.pre.pk}/estatut/", {"status": "EGZAMEN"})
        self.assertRedirects(response, f"/preinscriptions/{self.pre.pk}/")
        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, "EGZAMEN")

    def test_convert_creates_student_and_parent(self):
        response = self.client.post(f"/preinscriptions/{self.pre.pk}/konveti/")
        self.assertRedirects(response, f"/preinscriptions/{self.pre.pk}/")
        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, "INSCRIT")
        self.assertIsNotNone(self.pre.converted_student)
        self.assertTrue(Student.objects.filter(first_name="Marie", last_name="Jean").exists())
        self.assertTrue(Parent.objects.filter(first_name="Paul").exists())
        self.assertTrue(ParentStudent.objects.filter(student=self.pre.converted_student).exists())
