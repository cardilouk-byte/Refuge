from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from students.models import Student

from .models import Book, Loan

User = get_user_model()


class LibraryTest(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "admin@lnfcl.edu.ht", "AdminLNFCL2026!")
        self.direction = User.objects.create_user("direction", password="Direction2026!", role="DIRECTION")
        self.student_user = User.objects.create_user("eleve1", password="Eleve2026!", role="ELEVE")
        self.student = Student.objects.create(matricule="ELV-00001", first_name="Jean", last_name="Pierre", user=self.student_user)
        self.student2 = Student.objects.create(matricule="ELV-00002", first_name="Marie", last_name="Jean")
        self.book = Book.objects.create(title="Matematik 6èm", author="M. Pierre", total_copies=2)

    def test_direction_creates_book(self):
        self.client.login(username="direction", password="Direction2026!")
        response = self.client.post("/bibliotheque/nouveau/", {
            "title": "Istwa Ayiti", "author": "J. Casimir", "category": "Istwa", "total_copies": 3,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Book.objects.filter(title="Istwa Ayiti").exists())

    def test_borrow_and_return(self):
        self.client.login(username="direction", password="Direction2026!")
        self.client.post("/bibliotheque/prets/nouveau/", {
            "book": self.book.pk, "student": self.student.pk,
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
        }, follow=True)
        self.assertEqual(self.book.available_copies, 1)
        loan = Loan.objects.get(book=self.book, student=self.student)
        self.assertIsNone(loan.returned_at)
        self.client.post(f"/bibliotheque/prets/{loan.pk}/retourne/")
        loan.refresh_from_db()
        self.assertIsNotNone(loan.returned_at)
        self.assertEqual(self.book.available_copies, 2)

    def test_cannot_borrow_when_no_copies(self):
        Loan.objects.create(book=self.book, student=self.student, due_date=date.today() + timedelta(days=7))
        Loan.objects.create(book=self.book, student=self.student2, due_date=date.today() + timedelta(days=7))
        self.client.login(username="direction", password="Direction2026!")
        response = self.client.post("/bibliotheque/prets/nouveau/", {
            "book": self.book.pk, "student": self.student.pk,
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
        })
        self.assertContains(response, "Pa gen egzemplar")

    def test_eleve_cannot_access(self):
        self.client.login(username="eleve1", password="Eleve2026!")
        self.assertEqual(self.client.get("/bibliotheque/").status_code, 403)
