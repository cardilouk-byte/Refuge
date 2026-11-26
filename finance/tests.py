from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, Cycle, Level, Period, SchoolYear
from students.models import Parent, ParentStudent, Student
from teachers.models import Teacher

from .models import Expense, FeeType, Invoice, Payment

User = get_user_model()

HOST = {"HTTP_HOST": "localhost"}


class FinanceAccessTest(TestCase):
    def setUp(self):
        self.dir = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)
        self.prof = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")

    def test_anonymous_redirected(self):
        response = self.client.get("/finance/", **HOST)
        self.assertEqual(response.status_code, 302)

    def test_teacher_forbidden(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get("/finance/", **HOST)
        self.assertEqual(response.status_code, 403)

    def test_direction_sees_home_with_expenses(self):
        Expense.objects.create(label="Livre page", amount=Decimal("500"), category="FOURNITURES")
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/finance/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "500 HTG")
        self.assertContains(response, "Depans")


class ExpenseTest(TestCase):
    def setUp(self):
        self.dir = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)

    def test_create_expense(self):
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post(
            "/finance/depans/",
            {"label": "Espotyman", "category": "TRANSPORT", "amount": "2500", "spent_at": "2026-01-15"},
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(Expense.objects.first().label, "Espotyman")

    def test_delete_expense(self):
        e = Expense.objects.create(label="Bond", amount=Decimal("100"))
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.post(f"/finance/depans/{e.pk}/efase/", **HOST)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Expense.objects.count(), 0)


class InvoiceStatusTest(TestCase):
    def setUp(self):
        self.dir = User.objects.create_user("dir", password="Pass1234!", role="DIRECTION", is_staff=True)
        year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="1e Sik (1AF-3AF)", order=1)
        level = Level.objects.create(name="1e AF", cycle=cycle, order=1)
        classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
        self.student = Student.objects.create(matricule="ELV-00999", first_name="Ani", last_name="Tèst", classroom=classroom)
        self.fee = FeeType.objects.create(name="Inscription", amount=Decimal("5000"), school_year=year)

    def test_payment_updates_invoice_status_and_status_rows(self):
        invoice = Invoice.objects.create(student=self.student, fee_type=self.fee, amount=Decimal("5000"))
        self.assertEqual(invoice.status, "IMPAYE")
        Payment.objects.create(invoice=invoice, amount=Decimal("2000"))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "PARTIEL")
        Payment.objects.create(invoice=invoice, amount=Decimal("3000"))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "PAYE")

        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/finance/", **HOST)
        self.assertContains(response, "Payée")
        self.assertContains(response, "<span class=\"fw-bold\">1</span>")

    def test_status_badge_on_invoice_list(self):
        invoice = Invoice.objects.create(student=self.student, fee_type=self.fee, amount=Decimal("5000"))
        self.client.login(username="dir", password="Pass1234!")
        response = self.client.get("/finance/fakti/", **HOST)
        self.assertContains(response, "Poko")
