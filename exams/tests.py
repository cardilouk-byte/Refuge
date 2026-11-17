from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student

from .models import Exam

User = get_user_model()


class ExamsTest(TestCase):
    def setUp(self):
        self.year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="Fondamental")
        level = Level.objects.create(name="9ème AF", cycle=cycle)
        self.classroom = ClassRoom.objects.create(school_year=self.year, level=level, section="B")
        self.subject = Subject.objects.create(name="Français")
        self.period = Period.objects.create(school_year=self.year, name="Trimestre 1", order=1)
        User.objects.create_superuser("admin", "admin@lnfcl.edu.ht", "AdminLNFCL2026!")
        self.prof = User.objects.create_user("prof1", password="Prof2026!", role="ENSEIGNANT")
        self.student_user = User.objects.create_user("eleve1", password="Eleve2026!", role="ELEVE")
        Student.objects.create(matricule="ELV-00001", first_name="Marie", last_name="Jean", classroom=self.classroom, user=self.student_user)

    def test_prof_creates_exam(self):
        self.client.login(username="prof1", password="Prof2026!")
        response = self.client.post("/examens/nouveau/", {
            "classroom": self.classroom.pk, "subject": self.subject.pk, "period": self.period.pk,
            "title": "Egzamen Trimès 1", "exam_date": date.today().isoformat(),
            "duration_minutes": 120, "max_score": 20, "coefficient": 2,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Exam.objects.filter(title="Egzamen Trimès 1").exists())

    def test_student_sees_class_exams(self):
        Exam.objects.create(classroom=self.classroom, subject=self.subject, title="Egzamen Matematik", exam_date=date.today())
        self.client.login(username="eleve1", password="Eleve2026!")
        content = self.client.get("/examens/").content.decode()
        self.assertIn("Egzamen Matematik", content)

    def test_list_requires_login(self):
        self.assertEqual(self.client.get("/examens/").status_code, 302)
