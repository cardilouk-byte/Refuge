from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, Cycle, Level, SchoolYear, Subject
from students.models import Student

from .models import Devoir

User = get_user_model()


class BaseSetup(TestCase):
    def setUp(self):
        self.year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="Fondamental")
        level = Level.objects.create(name="6ème AF", cycle=cycle)
        self.classroom = ClassRoom.objects.create(school_year=self.year, level=level, section="A")
        self.subject = Subject.objects.create(name="Mathématiques")
        self.admin = User.objects.create_superuser("admin", "admin@lnfcl.edu.ht", "AdminLNFCL2026!")
        self.prof = User.objects.create_user("prof1", password="Prof2026!", role="ENSEIGNANT", first_name="P", last_name="T")
        self.student_user = User.objects.create_user("eleve1", password="Eleve2026!", role="ELEVE")
        self.student = Student.objects.create(
            matricule="ELV-00001", first_name="Jean", last_name="Pierre",
            classroom=self.classroom, user=self.student_user,
        )


class HomeworkTest(BaseSetup):
    def test_prof_can_create_devoir(self):
        self.client.login(username="prof1", password="Prof2026!")
        response = self.client.post("/devoirs/nouveau/", {
            "classroom": self.classroom.pk, "subject": self.subject.pk,
            "title": "Egzesis paj 12", "description": "Fè egzesis 1 rive 5",
            "due_date": date.today().isoformat(),
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Devoir.objects.filter(title="Egzesis paj 12").exists())

    def test_student_sees_only_own_class(self):
        other_level = Level.objects.create(name="NS1", cycle=Cycle.objects.create(name="Secondaire"))
        other_class = ClassRoom.objects.create(school_year=self.year, level=other_level, section="A")
        Devoir.objects.create(classroom=self.classroom, title="Pou klas mwen", due_date=date.today())
        Devoir.objects.create(classroom=other_class, title="Pou lot klas", due_date=date.today())
        self.client.login(username="eleve1", password="Eleve2026!")
        content = self.client.get("/devoirs/").content.decode()
        self.assertIn("Pou klas mwen", content)
        self.assertNotIn("Pou lot klas", content)

    def test_anonymous_redirected(self):
        response = self.client.get("/devoirs/")
        self.assertEqual(response.status_code, 302)

    def test_parent_cannot_create(self):
        self.client.login(username="eleve1", password="Eleve2026!")
        response = self.client.get("/devoirs/nouveau/")
        self.assertEqual(response.status_code, 403)
