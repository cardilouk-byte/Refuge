from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student
from teachers.models import Teacher

from .models import LessonEntry

User = get_user_model()
HOST = {"HTTP_HOST": "localhost"}


class CahiersTest(TestCase):
    def setUp(self):
        year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="1e Sik", order=1)
        level = Level.objects.create(name="3e AF", cycle=cycle, order=3)
        Period.objects.create(school_year=year, name="Trimès 1", order=1)
        self.classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
        subject = Subject.objects.create(name="Matematik")
        self.teacher_user = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        self.teacher = Teacher.objects.create(
            matricule="PROF-0001", first_name="Jean", last_name="Baptiste", user=self.teacher_user
        )
        self.cs = ClassSubject.objects.create(classroom=self.classroom, subject=subject, teacher=self.teacher)
        self.dir_user = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)

    def test_teacher_creates_entry(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.post(
            "/cahiers/nouveau/",
            {"class_subject": self.cs.pk, "date": "2025-12-08", "content": "Nou etidye ekasyon."},
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        entry = LessonEntry.objects.get()
        self.assertEqual(entry.status, LessonEntry.Status.ATTENTE)
        self.assertEqual(entry.created_by, self.teacher_user)

    def test_direction_verifies_entry_notifies_teacher(self):
        LessonEntry.objects.create(
            class_subject=self.cs, date="2025-12-08", content="Lekson 1", created_by=self.teacher_user
        )
        self.client.login(username="dir", password="Pass1234!")
        entry_id = LessonEntry.objects.get().pk
        response = self.client.post(
            f"/cahiers/verifye/{entry_id}/", {"action": "valide", "comment": "Bon travay"}, **HOST
        )
        self.assertEqual(response.status_code, 302)
        entry = LessonEntry.objects.get(pk=entry_id)
        self.assertEqual(entry.status, LessonEntry.Status.VALIDE)
        self.assertEqual(entry.reviewed_by, self.dir_user)
        self.assertTrue(self.teacher_user.notifications.filter(is_read=False).exists())

    def test_teacher_cannot_verify(self):
        LessonEntry.objects.create(class_subject=self.cs, date="2025-12-08", content="Lekson")
        self.client.login(username="prof", password="Pass1234!")
        entry_id = LessonEntry.objects.get().pk
        response = self.client.post(f"/cahiers/verifye/{entry_id}/", {"action": "valide"}, **HOST)
        self.assertEqual(response.status_code, 403)

    def test_cahier_excel_export(self):
        LessonEntry.objects.create(class_subject=self.cs, date="2025-12-08", content="Lekson 1")
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/cahiers/excel/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])
        self.assertGreater(len(response.content), 500)
