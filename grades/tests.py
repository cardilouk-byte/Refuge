from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student

from .models import CarnetSettings, Grade

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
        # mwayèn jeneral an sou /10: 14,33 /20 → 7,17 /10
        self.assertContains(response, "Mway\u00e8n jeneral /10")
        self.assertContains(response, "7,17")

    def test_bulletin_locked_for_unpaid_student(self):
        from finance.models import FeeType, Invoice

        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        fee = FeeType.objects.create(name="Frais scolarit\u00e9", amount=5000, school_year=self.d["year"])
        user = User.objects.create_user("elv1", password="Pass1234!", role="ELEVE")
        self.d["s1"].user = user
        self.d["s1"].save(update_fields=["user"])
        Invoice.objects.create(student=self.d["s1"], fee_type=fee, amount=5000)
        self.client.login(username="elv1", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bloke")
        self.assertNotContains(response, "Matematik")
        # rele sik tou bloke
        response = self.client.get(f"/notes/bulletin/cik/{self.d['s1'].pk}/", **HOST)
        self.assertContains(response, "bloke")
        # apre paye — bulletin an louvri
        inv = Invoice.objects.get()
        inv.status = "PAYE"
        inv.save()
        response = self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST)
        self.assertContains(response, "Matematik")

    def test_staff_not_locked_by_unpaid(self):
        from finance.models import FeeType, Invoice

        Grade.objects.create(
            student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], kind="DEVOIR", score=16
        )
        fee = FeeType.objects.create(name="Frais scolarit\u00e9", amount=5000, school_year=self.d["year"])
        Invoice.objects.create(student=self.d["s1"], fee_type=fee, amount=5000)
        self.client.login(username="adm", password="Pass1234!")
        response = self.client.get(f"/notes/bulletin/eleve/{self.d['s1'].pk}/", **HOST)
        self.assertContains(response, "Matematik")

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


class HonourTest(TestCase):
    def setUp(self):
        self.d = _setup_data()
        self.period = self.d["period"]
        self.classroom = self.d["classroom"]
        self.math = self.d["cs_math"]
        self.prof = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        self.parent = User.objects.create_user("parent1", password="Pass1234!", role="PARENT")

    def test_anonymous_redirected(self):
        response = self.client.get("/notes/tablo-done/", **HOST)
        self.assertEqual(response.status_code, 302)

    def test_parent_forbidden(self):
        self.client.login(username="parent1", password="Pass1234!")
        response = self.client.get("/notes/tablo-done/", **HOST)
        self.assertEqual(response.status_code, 403)

    def test_honour_shows_top_students_with_avg_10(self):
        Grade.objects.create(
            student=self.d["s1"], class_subject=self.math, period=self.period, score="16"
        )
        Grade.objects.create(
            student=self.d["s2"], class_subject=self.math, period=self.period, score="9"
        )
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get(f"/notes/tablo-done/?periyod={self.period.pk}", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jean Baptiste")
        self.assertNotContains(response, "Marie Clerger")

    def test_honour_empty_when_no_grades(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get("/notes/tablo-done/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pa gen el")


class CarnetTest(TestCase):
    def setUp(self):
        self.d = _setup_data()
        self.dir_user = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION")
        self.period2 = Period.objects.create(school_year=self.d["year"], name="Trimestre 2", order=2)
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], score="15")
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_fr"], period=self.d["period"], score="12")
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_math"], period=self.period2, score="11")
        self.s1 = self.d["s1"]

    def test_settings_page_and_edit(self):
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/notes/carnet/model/", **HOST)
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/notes/carnet/model/", {
            "school_name": "Lycée National François Cappoix de Limonade",
            "slogan": "VERS L'EXCELLENCE !",
            "subtitle": "Carnet Scolaire — 2e cycle",
            "address": "Limonade, Haïti",
            "tel1": "+509 3700-0000", "tel2": "", "email": "contact@lnfcl.edu.ht",
            "footer_motto": "LNFCL c'est l'excellence !",
            "reglements_text": "1.Arrivée à 7h30\n2.Uniforme obligatoire",
            "show_graph": "on", "show_photo": "on",
            "directeur": "M. Le Directeur Général", "border_color": "#1f2937",
        }, **HOST)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CarnetSettings.objects.count(), 1)
        carnet = CarnetSettings.load()
        self.assertEqual(carnet.subtitle, "Carnet Scolaire — 2e cycle")
        self.assertIn("Uniforme", carnet.reglements_text)

    def test_carnet_print_pages(self):
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{self.s1.pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("ELV-00001", html)
        self.assertIn("Matematik", html)
        self.assertIn("1er cycle", html)
        self.assertIn("2e cycle", html)
        self.assertIn("EXTRAITS DES R\u00c8GLEMENTS", html)
        self.assertIn("OBSERVATIONS", html)
        self.assertIn("Moyenne de l'élève", html)
        self.assertNotIn("Examen Officiels", html)

    def test_carnet_print_denied_for_other_students(self):
        User.objects.create_user("eleve2", password="Pass1234!", role="ELEVE")
        self.client.login(username="eleve2", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{self.s1.pk}/", **HOST)
        self.assertEqual(response.status_code, 403)

    def test_official_section_for_ns4(self):
        from decimal import Decimal

        from teachers.models import Teacher
        level_ns4 = Level.objects.create(name="NS4", cycle=self.d["cycle2"], order=10)
        classroom_ns4 = ClassRoom.objects.create(school_year=self.d["year"], level=level_ns4, section="A")
        teacher = Teacher.objects.create(matricule="PROF-01", first_name="Paul", last_name="Hilaire")
        cs_ns4 = ClassSubject.objects.create(classroom=classroom_ns4, subject=self.d["math"], coefficient=4, teacher=teacher)
        st_ns4 = Student.objects.create(matricule="ELV-00010", first_name="Kerby", last_name="Louis", classroom=classroom_ns4)
        Grade.objects.create(student=st_ns4, class_subject=cs_ns4, period=self.d["period"], kind="EXAMEN", score=Decimal("14.5"))
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{st_ns4.pk}/", **HOST)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("EXAMEN OFFICIELS", html)
        self.assertIn("Paul Hilaire", html)
        self.assertIn("examenChart", html)
        self.assertIn("Filière", html)


class CarnetPDFTest(TestCase):
    def setUp(self):
        from decimal import Decimal

        self.d = _setup_data()
        self.dir_user = User.objects.create_user("dir2", password="Pass1234!", role="DIRECTION")
        period = self.d["period"]
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_math"], period=period, score="15")
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_fr"], period=period, score="10")
        Grade.objects.create(student=self.d["s2"], class_subject=self.d["cs_math"], period=period, score="8")

    def test_pdf_lekti(self):
        self.client.login(username="dir2", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{self.d['s1'].pk}/pdf/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertGreater(len(response.content), 800)

    def test_pdf_livret_imposition(self):
        self.client.login(username="dir2", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{self.d['s1'].pk}/pdf/?mod=livret", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        # entepozisyon an ka pwodui yon fichye diferan (paj vid + paj A4)
        base = self.client.get(f"/notes/carnet/eleve/{self.d['s1'].pk}/pdf/", **HOST)
        self.assertNotEqual(len(response.content), len(base.content))

    def test_pdf_denied_for_other_students(self):
        User.objects.create_user("eleve3", password="Pass1234!", role="ELEVE")
        self.client.login(username="eleve3", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/eleve/{self.d['s1'].pk}/pdf/", **HOST)
        self.assertEqual(response.status_code, 403)

    def test_class_pdf_batch(self):
        self.client.login(username="dir2", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/klas/{self.d['classroom'].pk}/pdf/?mod=livret", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        # clas la gen 2 elèv — PDF sa a fòse pi gran pase yon sèl karnè
        solo = self.client.get(f"/notes/carnet/eleve/{self.d['s1'].pk}/pdf/?mod=livret", **HOST)
        self.assertGreater(len(response.content), len(solo.content))

    def test_class_pdf_denied_for_students(self):
        User.objects.create_user("eleve4", password="Pass1234!", role="ELEVE")
        self.client.login(username="eleve4", password="Pass1234!")
        response = self.client.get(f"/notes/carnet/klas/{self.d['classroom'].pk}/pdf/", **HOST)
        self.assertEqual(response.status_code, 403)
