from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student

User = get_user_model()

HOST = {"HTTP_HOST": "localhost"}


def _setup_data():
    year = SchoolYear.objects.create(label="2025-2026", is_current=True)
    cycle = Cycle.objects.create(name="2e Sik (4AF-6AF)", order=2)
    level = Level.objects.create(name="6e AF", cycle=cycle, order=6)
    period = Period.objects.create(school_year=year, name="Trim\u00e8s 1", order=1)
    classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
    math = Subject.objects.create(name="Matematik", code="MATH")
    fr = Subject.objects.create(name="Franse", code="FR")
    cs_math = ClassSubject.objects.create(classroom=classroom, subject=math, coefficient=4)
    cs_fr = ClassSubject.objects.create(classroom=classroom, subject=fr, coefficient=2)
    s1 = Student.objects.create(matricule="ELV-00001", first_name="Jean", last_name="Baptiste", classroom=classroom)
    s2 = Student.objects.create(matricule="ELV-00002", first_name="Marie", last_name="Clerger", classroom=classroom)
    return {
        "year": year, "cycle": cycle, "level": level, "period": period,
        "classroom": classroom, "math": math, "fr": fr,
        "cs_math": cs_math, "cs_fr": cs_fr, "s1": s1, "s2": s2,
    }


class ApiTest(TestCase):
    def setUp(self):
        from finance.models import FeeType, Invoice
        from grades.models import Grade

        self.d = _setup_data()
        self.dir_user = User.objects.create_user("dirapi", password="Pass1234!", role="DIRECTION")
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_math"], period=self.d["period"], score="15")
        Grade.objects.create(student=self.d["s1"], class_subject=self.d["cs_fr"], period=self.d["period"], score="12")
        self.fee = FeeType.objects.create(name="Frais scolarite", amount=5000, school_year=self.d["year"])
        self.invoice = Invoice.objects.create(student=self.d["s1"], fee_type=self.fee, amount=5000)

    def test_ping_public(self):
        r = self.client.get("/api/ping/", **HOST)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertTrue(j["ok"])
        self.assertEqual(j["service"], "LNFCL SIGES API")

    def test_stats_requires_staff(self):
        r = self.client.get("/api/stats/", **HOST)
        self.assertEqual(r.status_code, 403)
        User.objects.create_user("elevapi", password="Pass1234!", role="ELEVE")
        self.client.login(username="elevapi", password="Pass1234!")
        r = self.client.get("/api/stats/", **HOST)
        self.assertEqual(r.status_code, 403)

    def test_stats_values(self):
        self.client.login(username="dirapi", password="Pass1234!")
        r = self.client.get("/api/stats/", **HOST)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j["tota"]["el\u00e8v"], 2)
        self.assertEqual(j["tota"]["klas"], 1)
        self.assertEqual(j["finans"]["fakti_poko_peye"], 1)
        self.assertEqual(j["anne_kouran"], "2025-2026")

    def test_nivo_klas_matye(self):
        self.client.login(username="dirapi", password="Pass1234!")
        r = self.client.get("/api/nivo/", **HOST)
        j = r.json()
        self.assertEqual(j["syik"][0]["syik"], "2e Sik (4AF-6AF)")
        self.assertEqual(j["syik"][0]["nivo"][0]["non"], "6e AF")
        r = self.client.get("/api/klas/", **HOST)
        j = r.json()
        self.assertEqual(len(j["klas"]), 1)
        self.assertEqual(j["klas"][0]["el\u00e8v"], 2)
        self.assertEqual(len(j["klas"][0]["matye"]), 2)
        r = self.client.get("/api/matye/", **HOST)
        j = r.json()
        self.assertEqual(len(j["matye"]), 2)

    def test_elev_by_matricule(self):
        self.client.login(username="dirapi", password="Pass1234!")
        r = self.client.get("/api/elev/ELV-00001/", **HOST)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j["non"], "Baptiste")
        self.assertEqual(j["moyen_pa_p\u00e9ry\u00f2d"][0]["moyen_j\u00e9neral"], 14.0)
        self.assertFalse(j["tout_f\u00e8_peye"])
        r = self.client.get("/api/elev/ELV-99999/", **HOST)
        self.assertEqual(r.status_code, 404)

    def test_bulletin_values_and_rank(self):
        from grades.models import Grade

        Grade.objects.create(student=self.d["s2"], class_subject=self.d["cs_math"], period=self.d["period"], score="10")
        Grade.objects.create(student=self.d["s2"], class_subject=self.d["cs_fr"], period=self.d["period"], score="10")
        self.client.login(username="dirapi", password="Pass1234!")
        r = self.client.get("/api/bulletin/ELV-00001/", **HOST)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j["el\u00e8v"], "Jean Baptiste")
        b = j["bulletin"][0]
        self.assertEqual(b["moyen_j\u00e9neral"], 14.0)
        self.assertEqual(b["plas"], 1)
        self.assertEqual(b["sou"], 2)
        self.assertEqual(b["line"][0]["koef"], 2)  # Franse \u2014 l\u00f2d alfabetik
        self.assertEqual(b["line"][1]["moyen"], 15.0)  # Matematik

    def test_docs_page(self):
        self.client.login(username="dirapi", password="Pass1234!")
        r = self.client.get("/api/", **HOST)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "/api/ping/")
        self.assertContains(r, "/api/bulletin/")
