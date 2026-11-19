from django.contrib.auth import get_user_model
from django.test import TestCase

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from students.models import Student
from teachers.models import Teacher

from .models import Attempt, Question, Quiz

User = get_user_model()
HOST = {"HTTP_HOST": "localhost"}


class QuizzesTest(TestCase):
    def setUp(self):
        year = SchoolYear.objects.create(label="2025-2026", is_current=True)
        cycle = Cycle.objects.create(name="1e Sik", order=1)
        level = Level.objects.create(name="3e AF", cycle=cycle, order=3)
        Period.objects.create(school_year=year, name="Trimestre 1", order=1)
        self.classroom = ClassRoom.objects.create(school_year=year, level=level, section="A")
        subject = Subject.objects.create(name="Matematik")
        self.prof = User.objects.create_user("prof", password="Pass1234!", role="ENSEIGNANT")
        teacher = Teacher.objects.create(
            matricule="PROF-0001", first_name="Jean", last_name="Baptiste", user=self.prof
        )
        self.cs = ClassSubject.objects.create(
            classroom=self.classroom, subject=subject, teacher=teacher
        )
        self.student_user = User.objects.create_user("jibap", password="Pass1234!", role="ELEVE")
        self.student = Student.objects.create(
            matricule="ELV-00201", first_name="Jean", last_name="Jeanbapt", user=self.student_user,
            classroom=self.classroom,
        )

    def _make_quiz(self, published=True):
        quiz = Quiz.objects.create(
            classroom=self.classroom, class_subject=self.cs, title="Televizyon 1", created_by=self.prof
        )
        Question.objects.create(
            quiz=quiz, text="2+2?", option_a="3", option_b="4", option_c="5", option_d="6",
            correct="B", points=1, order=1,
        )
        Question.objects.create(
            quiz=quiz, text="Kapital Ayiti?", option_a="Parye", option_b="Kanpe", option_c="Pòtoprens",
            option_d="Kapè", correct="C", points=2, order=2,
        )
        if published:
            quiz.is_published = True
            quiz.save()
        return quiz

    def test_teacher_full_workflow(self):
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.post(
            "/quiz/nouveau/",
            {
                "classroom": self.classroom.pk, "class_subject": self.cs.pk, "title": "Test Vite",
                "description": "Kontwòl rapid", "due_date": "2025-12-19",
            },
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        quiz = Quiz.objects.get(title="Test Vite")
        self.assertEqual(quiz.created_by, self.prof)
        self.assertFalse(quiz.is_published)
        self.assertEqual(
            self.client.get(f"/quiz/{quiz.pk}/kesyon/", **HOST).status_code, 200
        )
        response = self.client.post(
            f"/quiz/{quiz.pk}/kesyon/",
            {"text": "1+1?", "option_a": "1", "option_b": "2", "option_c": "3", "option_d": "4",
             "correct": "B", "points": 1, "order": 1},
            **HOST,
        )
        self.assertEqual(response.status_code, 302)
        quiz = Quiz.objects.get(title="Test Vite")
        self.assertEqual(quiz.questions.count(), 1)
        response = self.client.post(f"/quiz/{quiz.pk}/publie/", **HOST)
        self.assertEqual(response.status_code, 302)
        quiz.refresh_from_db()
        self.assertTrue(quiz.is_published)
        self.assertTrue(
            self.student_user.notifications.filter(url=f"/quiz/{quiz.pk}/fe/").exists()
        )

    def test_student_takes_quiz_auto_graded(self):
        quiz = self._make_quiz()
        q1, q2 = list(quiz.questions.all())
        self.client.login(username="jibap", password="Pass1234!")
        response = self.client.get(f"/quiz/{quiz.pk}/fe/", **HOST)
        self.assertContains(response, "2+2?")
        response = self.client.post(
            f"/quiz/{quiz.pk}/fe/", {f"ans_{q1.pk}": "B", f"ans_{q2.pk}": "A"}, **HOST
        )
        self.assertEqual(response.status_code, 200)
        attempt = Attempt.objects.get(quiz=quiz, student=self.student)
        self.assertEqual(str(attempt.score), "1.00")
        self.assertEqual(str(attempt.total), "3.00")
        self.assertTrue(
            self.prof.notifications.filter(title__contains=self.student.full_name).exists()
        )
        # repons sofwa — pa ka fe l ankò
        response = self.client.get(f"/quiz/{quiz.pk}/fe/", **HOST)
        self.assertContains(response, "fini")

    def test_eleve_cannot_take_other_class_quiz(self):
        quiz = self._make_quiz()
        other_user = User.objects.create_user("other", password="Pass1234!", role="ELEVE")
        Student.objects.create(matricule="ELV-00202", first_name="Marie", last_name="Clerger")
        self.client.login(username="other", password="Pass1234!")
        response = self.client.get(f"/quiz/{quiz.pk}/fe/", **HOST)
        self.assertEqual(response.status_code, 403)

    def test_unpublished_quiz_hidden_from_eleve(self):
        quiz = self._make_quiz(published=False)
        self.client.login(username="jibap", password="Pass1234!")
        response = self.client.get("/quiz/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, quiz.title)

    def test_quiz_excel_export(self):
        quiz = self._make_quiz()
        Attempt.objects.create(quiz=quiz, student=self.student, score=2, total=3)
        self.client.login(username="prof", password="Pass1234!")
        response = self.client.get(f"/quiz/{quiz.pk}/rezilta/excel/", **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])
        self.assertGreater(len(response.content), 500)
