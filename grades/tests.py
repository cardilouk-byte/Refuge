from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student

from .models import Grade

User = get_user_model()

HOST = {"HTTP_HOST": "localhost"}


def _setup_data():
    year = SchoolYear.objects.create(label="2025-2026", is_current=True)
    cycle1 = Cycle.objects.create(name="1e Sik (1AF-3AF)", order=1)
    cycle2 = Cycle.objects.create(name="2e Sik (4AF-6AF)", order=2)
    level6 = Level.objects.create(name="6e AF", cycle=cycle2, order=6)
    period = Period.objects.create(school_year=year, name="Trimès 1", order=1)
    classroom = ClassRoom.objects.create(school_year=year, level=level6, section="A")
    math = Subject.objects.create(name="Matematik", code="MATH")
    fr = Subject.objects.create(name="Franse", code="FR")
    cs_math = ClassSubject.objects.create(classroom=classroom, subject=math, coefficient=4)
    cs_fr = ClassSubject.objects.create(classroom=classroom, subject=fr, coefficient=2)
    s1 = Student.objects.create(matricule="ELV-00001", first_name="Jean", last_name="Baptiste", classroom=classroom)
    s2 = Student.objects.create(matricule="ELV-00002", first_name="Marie", last_name="Clerger", classroom=classroom)
    return {
        "year": year, "cycle1": cycle1, "cycle2": cycle2, "level6": level6,
        "period": period, "classroom": classroom, "math": math, "fr": fr,
        "cs_math": cs_math, "cs_fr": cs_fr, "s1": s1, "s2": s2,
    }


class NotesSaisieTest(TestCase):
    def setUp(self):
        d = _setup_data()
        self.d = d
        self.prof = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        self.eleve_user = User.objects.create_user("eleve1", password="Pass1234!", role="ELEVE")

    def test_prof_sees_class_list(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get("/notes/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "6e AF")

    def test_saisie_page_and_post_saves_grades(self):
        self.client.login(username="prof", password="Pass1234!")
        url = f"/notes/klas/{self.d['classroom'].pk}/?periyod={self.d['period'].pk}&matye={self.d['cs_math'].pk}"
        response = self.client.get(url, **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ELV-00001")
        response = self.client.post(
            url,
            {
                "periyod": self.d["period"].pk,
                "matye": self.d["cs_math"].pk,
                "tip": "DEVOIR",
                f"note_{self.d['s1'].pk}": "15",
                f"note_{self.d['s2'].pk}": "12,5",
            },
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        g1 = Grade.objects.get(student=self.d["s1"])
        self.assertEqual(str(g1.score), "15.00")
        g2 = Grade.objects.get(student=self.d["s2"])
        self.assertEqual(str(g2.score), "12.50")
        self.assertEqual(g2.kind, "DEVOIR")

    def test_invalid_score_rejected(self):
        self.client.login(username="prof", password="Pass1234!")
        url = f"/notes/klas/{self.d['classroom'].pk}/?periyod={self.d['period'].pk}&matye={self.d['cs_math'].pk}"
        response = self.client.post(
            url,
            {
                "periyod": self.d["period"].pk,
                "matye": self.d["cs_math"].pk,
                "tip": "DEVOIR",
                f"note_{self.d['s1'].pk}": "25",
            },
            follow=True,
            **HOST,
        )
        self.assertFalse(Grade.objects.exists())
        self.assertContains(response, "Nòt pa sove")

    def test_eleve_cannot_enter_grades(self):
        self.client.login(username="eleve1", password="Pass1234!")
        response = self.client.get(f"/notes/klas/{self.d['classroom'].pk}/", **HOST)
        self.assertEqual(response.status_code, 403)


class BulletinTest(TestCase):
    def setUp(self):
        d = _setup_data()
        self.d = d
        self.admin = User.objects.create_superuser("adm", "a@a.ht", "Pass1234!")
        self.parent_user = User.objects.create_user("pap", password="Pass1234!", role="PARENT")
        from students.models import Parent, ParentStudent

        parent = Parent.objects.create(first_name="Papa", last_name="Baptiste", user=self.parent_user)
        ParentStudent.objects.create(parent=parent, student=d["s1"], is_primary=True)

    def test_bulletin_shows_moyenne_and_admis(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="EXAMEN", score=15
        )
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_fr"], period=self.d["period"], kind="DEVOIR", score=12
        )
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ADMIS")
        self.assertContains(response, "Matematik")
        self.assertContains(response, "15,50")

    def test_bulletin_redouble_score(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=6
        )
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST)
        self.assertContains(response, "REDOBLE")

    def test_bulletin_class_ranking(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        Grade.objects.create(
            student=self.d["s2"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=10
        )
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/klas/{self.d['classroom'].pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index("Jean"), content.index("Marie"))

    def test_eleve_sees_own_bulletin_only(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        user_s1 = User.objects.create_user("jibap", password="Pass1234!", role="ELEVE")
        self.d["s1"].user = user_s1
        self.d["s1"].save()
        self.client.login(username="jibap", password="Pass1234!")
        self.assertEqual(self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST).status_code, 200)
        self.assertEqual(self.client.get(f"/notes/bulletin/eleve/{self.d['s2'].pk}/", **HOST).status_code, 403)

    def test_parent_sees_child_bulletin(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        self.client.login(username="pap", password="Pass1234!")
        self.assertEqual(self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST).status_code, 200)
        self.assertEqual(self.client.get(f"/notes/bulletin/eleve/{self.d['s2'].pk}/", **HOST).status_code, 403)

    def test_bulletin_cycle_decision(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/cik/{self.d['s1'].pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DESIZYON SIK")
        self.assertContains(response, "ADMIS")
