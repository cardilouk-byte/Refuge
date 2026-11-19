from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, SchoolYear, Subject
from students.models import Student

User = get_user_model()
HOST = {"HTTP_HOST": "localhost"}


class PromotionTest(TestCase):
    def setUp(self):
        self.year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="1e Sik", order=1)
        self.level1 = Level.objects.create(name="6e AF", cycle=cycle, order=6)
        self.level2 = Level.objects.create(name="5e AF", cycle=cycle, order=7)
        self.room1 = ClassRoom.objects.create(school_year=self.year, level=self.level1, section="A")
        subject = Subject.objects.create(name="Matematik")
        self.cs = ClassSubject.objects.create(classroom=self.room1, subject=subject, coefficient=2)
        self.staff_user = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)
        self.eleve_user = User.objects.create_user("jibap", password="Pass1234!", role="ELEVE")
        self.st_mont = Student.objects.create(
            matricule="ELV-00001", first_name="Jean", last_name="Mont", classroom=self.room1,
            user=self.eleve_user,
        )
        self.st_repeat = Student.objects.create(
            matricule="ELV-00002", first_name="Marie", last_name="Again", classroom=self.room1
        )
        self.st_leave = Student.objects.create(
            matricule="ELV-00003", first_name="Paul", last_name="Depart", classroom=self.room1
        )

    def _new_year(self):
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post("/nouvel-ane/nouvye/", {"label": "2026-2027", "copy_classrooms": "on"}, **HOST)
        self.assertEqual(response.status_code, 302)
        return SchoolYear.objects.get(label="2026-2027")

    def test_new_year_copies_classrooms_and_subjects(self):
        new_year = self._new_year()
        rooms = ClassRoom.objects.filter(school_year=new_year)
        self.assertEqual(rooms.count(), 1)
        new_room = rooms.get()
        self.assertEqual((new_room.level, new_room.section), (self.level1, "A"))
        self.assertTrue(
            ClassSubject.objects.filter(
                classroom=new_room, subject=self.cs.subject, coefficient=2
            ).exists()
        )
        # anien klase a pa deplase
        self.room1.refresh_from_db()
        self.assertEqual(self.room1.school_year, self.year)

    def test_new_year_requires_staff(self):
        self.client.login(username="jibap", password="Pass1234!")
        self.assertEqual(self.client.get("/nouvel-ane/nouvye/", **HOST).status_code, 403)

    def test_transition_page(self):
        new_year = self._new_year()
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get(
            f"/nouvel-ane/pasaj/?anvye={self.year.pk}&novel={new_year.pk}", **HOST
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jean")

    def test_apply_mont_redouble_kite(self):
        new_year = self._new_year()
        top = ClassRoom.objects.create(school_year=new_year, level=self.level2, section="A")
        repeat = ClassRoom.objects.filter(school_year=new_year, level=self.level1, section="A").get()
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post(
            "/nouvel-ane/pasaj/aplike/",
            {
                "old_year": self.year.pk, "new_year": new_year.pk,
                f"act_{self.st_mont.pk}": "MONT",
                f"act_{self.st_repeat.pk}": "REDOUBLE",
                f"act_{self.st_leave.pk}": "KITE",
            },
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        self.st_mont.refresh_from_db()
        self.st_repeat.refresh_from_db()
        self.st_leave.refresh_from_db()
        self.assertEqual(self.st_mont.classroom, top)
        self.assertEqual(self.st_mont.status, "ACTIF")
        self.assertEqual(self.st_repeat.classroom, repeat)
        self.assertEqual(self.st_repeat.status, "ACTIF")
        self.assertEqual(self.st_leave.status, "ARCHIVE")
        # ane nèf la vin aktyèl, aniye a pa
        new_year.refresh_from_db()
        self.year.refresh_from_db()
        self.assertTrue(new_year.is_current)
        self.assertFalse(self.year.is_current)

    def test_apply_default_is_mont(self):
        new_year = self._new_year()
        ClassRoom.objects.create(school_year=new_year, level=self.level2, section="A")
        self.client.login(username="dir", password="Pass1234!")
        self.client.post(
            "/nouvel-ane/pasaj/aplike/", {"old_year": self.year.pk, "new_year": new_year.pk}, **HOST
        )
        self.st_mont.refresh_from_db()
        self.assertEqual(self.st_mont.classroom.level, self.level2)

    def test_detail_page(self):
        new_year = self._new_year()
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get(
            f"/nouvel-ane/klas/{self.room1.pk}/?novel={new_year.pk}", **HOST
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Marie")
        self.client.logout()
        self.assertEqual(self.client.get("/nouvel-ane/klas/%d/" % self.room1.pk, **HOST).status_code, 302)
