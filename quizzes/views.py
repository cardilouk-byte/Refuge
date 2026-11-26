from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import teaching_staff_required
from notifications.models import Notification
from students.models import Student

from .forms import QuestionForm, QuizForm
from .models import Attempt, Question, Quiz

User = get_user_model()


def _visible_quizzes(user):
    if user.is_authenticated and user.role == User.Role.ELEVE:
        st = getattr(user, "student_profile", None)
        if not st or not st.classroom:
            return Quiz.objects.none()
        return Quiz.objects.filter(classroom=st.classroom, is_published=True)
    if user.is_authenticated and user.role == User.Role.PARENT:
        students = Student.objects.filter(parentstudent__parent__user=user)
        return Quiz.objects.filter(classroom__students__in=students, is_published=True).distinct()
    return Quiz.objects.all().select_related("classroom", "class_subject", "created_by")


@login_required
def quiz_list(request):
    quizzes = _visible_quizzes(request.user)
    can_manage = request.user.is_teaching_staff or request.user.is_staff
    student = getattr(request.user, "student_profile", None)
    attempts = {}
    if student:
        attempts = {a.quiz_id: a for a in Attempt.objects.filter(student=student)}
    for q in quizzes:
        q.nb_questions = q.questions.count()
    return render(
        request,
        "quizzes/list.html",
        {"quizzes": quizzes, "can_manage": can_manage, "attempts": attempts, "student": student},
    )


@teaching_staff_required
def quiz_create(request):
    form = QuizForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.created_by = request.user
        quiz.save()
        messages.success(request, "Quiz kreye — kounye a ajoute kesyon yo.")
        return redirect("quizzes:questions", quiz.pk)
    return render(request, "quizzes/form.html", {"form": form, "titre": "Nouvo quiz"})


@teaching_staff_required
def quiz_update(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuizForm(request.POST or None, instance=quiz, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Quiz mete ajou.")
        return redirect("quizzes:list")
    return render(request, "quizzes/form.html", {"form": form, "titre": "Modifye quiz"})


@teaching_staff_required
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        quiz.delete()
        messages.success(request, "Quiz efase.")
        return redirect("quizzes:list")
    return render(request, "quizzes/confirm_delete.html", {"object": quiz})


@teaching_staff_required
def quiz_questions(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.quiz = quiz
        question.save()
        messages.success(request, "Kesyon ajoute.")
        return redirect("quizzes:questions", quiz.pk)
    questions = quiz.questions.all()
    return render(request, "quizzes/questions.html", {"quiz": quiz, "form": form, "questions": questions})


@teaching_staff_required
def question_delete(request, quiz_pk, pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    question = get_object_or_404(Question, pk=pk, quiz=quiz)
    if request.method == "POST":
        question.delete()
        messages.success(request, "Kesyon efase.")
    return redirect("quizzes:questions", quiz.pk)


@teaching_staff_required
def quiz_publish(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "POST":
        quiz.is_published = not quiz.is_published
        quiz.save()
        if quiz.is_published:
            students = quiz.classroom.students.filter(status="ACTIF")
            Notification.send_many(
                [s.user for s in students if s.user],
                f"Quiz nouvo: {quiz.title}",
                body=f"Ou gen yon quiz pou fe nan {quiz.classroom}.",
                url=f"/quiz/{quiz.pk}/fe/",
            )
            messages.success(request, "Quiz pibliye — elèv yo resevwa yon notifikasyon.")
        else:
            messages.success(request, "Quiz depibliye.")
    return redirect("quizzes:list")


@login_required
def quiz_take(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("classroom"), pk=pk)
    student = getattr(request.user, "student_profile", None)
    is_staff = request.user.is_staff or request.user.is_school_staff
    if not (student and student.classroom_id == quiz.classroom_id) and not is_staff:
        raise PermissionDenied
    attempt = Attempt.objects.filter(quiz=quiz, student=student).first() if student else None
    questions = quiz.questions.all()
    if not questions:
        return render(request, "quizzes/empty.html", {"quiz": quiz})
    if request.method == "POST" and student and not attempt:
        score = 0
        total = sum(q.points for q in questions)
        for q in questions:
            chosen = request.POST.get(f"ans_{q.pk}", "").strip().upper()
            if chosen == q.correct:
                score += q.points
        attempt = Attempt.objects.create(quiz=quiz, student=student, score=Decimal(score), total=Decimal(total))
        if quiz.created_by:
            Notification.send(
                quiz.created_by,
                f"Quiz: {student.full_name} fini « {quiz.title} »",
                body=f"Rezilta: {score}/{total}",
                url=f"/quiz/{quiz.pk}/rezilta/",
            )
        return render(request, "quizzes/result.html", {"quiz": quiz, "attempt": attempt})
    if attempt:
        return render(request, "quizzes/result.html", {"quiz": quiz, "attempt": attempt})
    if not quiz.is_published and not is_staff:
        raise PermissionDenied
    return render(request, "quizzes/take.html", {"quiz": quiz, "questions": questions})


@teaching_staff_required
def quiz_results(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    attempts = quiz.attempts.select_related("student").order_by("-score")
    students = list(quiz.classroom.students.filter(status="ACTIF"))
    done = {a.student_id for a in attempts}
    missing = [s for s in students if s.pk not in done]
    return render(
        request,
        "quizzes/results.html",
        {"quiz": quiz, "attempts": attempts, "missing": missing},
    )


@teaching_staff_required
def quiz_excel(request, pk):
    from core.xlsx import xlsx_response

    quiz = get_object_or_404(Quiz.objects.select_related("classroom"), pk=pk)
    attempts = quiz.attempts.select_related("student").order_by("-score")
    rows = [
        [i + 1, a.student.matricule, a.student.full_name, float(a.score), float(a.total), a.percent]
        for i, a in enumerate(attempts)
    ]
    name = f"quiz_{quiz.title.strip().replace(' ', '_')[:30]}.xlsx"
    return xlsx_response(
        "Rezilta quiz", ["Rang", "Matricule", "Elèv", "Pwen", "Total", "%"], rows, name
    )
