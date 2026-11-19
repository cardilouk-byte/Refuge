from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from academics.models import ClassRoom, Cycle, Level, Period, SchoolYear, Subject, ClassSubject
from students.models import Student

from .models import AttendanceRecord

User = get_user_model()

HOST = {"HTTP_HOST": "localhost"}


def _setup_data():
    year = SchoolYear.objects.create(label="2025-2026", is_current=True)
    cycle = Cycle.objects.create(name="1e Sik (1AF-3AF)", order=1)
    level = Level.objects.create(name="3e AF", cycle=cycle, order=3)
    Period.objects.create(school_year=year, name="Trimès 1", order=1)
    classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
    subject = Subject.objects.create(name="Matematik")
    ClassSubject.objects.create(classroom=classroom, subject=subject)
    s1 = Student.objects.create(matricule="ELV-00101", first_name="Jean", last_name="Baptiste", classroom=classroom)
    s2 = Student.objects.create(matricule="ELV-00102", first_name="Marie", last_name="Clerger", classroom=classroom)
    return {"classroom": classroom, "s1": s1, "s2": s2}


class AttendanceTest(TestCase):
    def setUp(self):
        d = _setup_data()
        self.d = d
        self.prof = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        self.dir = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)

    def test_prof_class_list(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get("/presens/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3e AF")

    def test_take_post_saves_records(self):
        self.client.login(username="prof", password="Pass1234!")
        url = f"/presens/klas/{self.d['classroom'].pk}/"
        response = self.client.get(url, **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ELV-00101")
        response = self.client.post(
            url,
            {
                "dat": "2025-12-01",
                f"status_{self.d['s1'].pk}": "ABSENT",
                f"justifie_{self.d['s1'].pk}": "on",
                f"note_{self.d['s1'].pk}": "Li viktim sentòm la",
                f"status_{self.d['s2'].pk}": "RETARD",
            },
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        r1 = AttendanceRecord.objects.get(student=self.d["s1"], date="2025-12-01")
        self.assertEqual(r1.status, "ABSENT")
        self.assertTrue(r1.justified)
        r2 = AttendanceRecord.objects.get(student=self.d["s2"], date="2025-12-01")
        self.assertEqual(r2.status, "RETARD")

    def test_take_page_shows_existing_status(self):
        AttendanceRecord.objects.create(student=self.d["s1"], date=timezone.localdate(), status="RETARD")
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get(f"/presens/klas/{self.d['classroom'].pk}/", **HOST)
        html = response.content.decode()
        self.assertIn('value="RETARD" checked', html)

    def test_report_filters_records(self):
        AttendanceRecord.objects.create(
            student=self.d["s1"], date=timezone.localdate() - timedelta(days=1), status="ABSENT"
        )
        AttendanceRecord.objects.create(student=self.d["s1"], date=timezone.localdate(), status="RETARD")
        AttendanceRecord.objects.create(student=self.d["s2"], date=timezone.localdate(), status="PRESENT")
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get(f"/presens/rapor/?eleve={self.d['s1'].pk}", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(response.context["stats"])), 1)
        self.assertEqual(response.context["stats"][0]["student__matricule"], "ELV-00101")
        self.assertEqual(response.context["stats"][0]["absans"], 1)

    def test_eleve_sees_own_records(self):
        AttendanceRecord.objects.create(student=self.d["s1"], date=timezone.localdate(), status="ABSENT")
        user_s1 = User.objects.create_user("jibap", password="Pass1234!", role="ELEVE")
        self.d["s1"].user = user_s1
        self.d["s1"].save()
        self.client.login(username="jibap", password="Pass1234!")
        response = self.client.get("/presens/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Absan")
        self.assertEqual(self.client.get(f"/presens/klas/{self.d['classroom'].pk}/", **HOST).status_code, 403)
