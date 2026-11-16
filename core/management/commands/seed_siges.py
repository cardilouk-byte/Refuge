import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from attendance.models import AttendanceRecord
from finance.models import FeeType, Invoice, Payment
from grades.models import Grade
from students.models import Parent, ParentStudent, Student
from teachers.models import Teacher


class Command(BaseCommand):
    help = "Crée des données de démonstration pour le SIGES (comptes, classes, notes, finances)."

    def handle(self, *args, **options):
        User = get_user_model()
        random.seed(42)

        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"role": User.Role.SUPERADMIN, "is_staff": True, "is_superuser": True,
                      "first_name": "Administrateur", "last_name": "LNFCL"},
        )
        if created:
            admin.set_password("AdminLNFCL2026!")
            admin.save()

        direction, created = User.objects.get_or_create(
            username="direction",
            defaults={"role": User.Role.DIRECTION, "is_staff": True,
                      "first_name": "Marie", "last_name": "Jean-Pierre"},
        )
        if created:
            direction.set_password("Direction2026!")
            direction.save()

        teacher_users = []
        teacher_data = [
            ("prof1", "Jean", "Baptiste", "Mathématiques"),
            ("prof2", "Claire", "Pierre", "Français"),
            ("prof3", "Paul", "Louis", "Sciences"),
        ]
        for username, first, last, specialty in teacher_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"role": User.Role.ENSEIGNANT, "first_name": first, "last_name": last},
            )
            if created:
                user.set_password("Prof2026!")
                user.save()
            teacher, _ = Teacher.objects.get_or_create(
                matricule=f"ENS-{username.upper()}",
                defaults={"user": user, "first_name": first, "last_name": last, "specialty": specialty},
            )
            teacher_users.append((user, teacher))

        year, _ = SchoolYear.objects.get_or_create(label="2025-2026", defaults={"is_current": True})
        year.is_current = True
        year.save()

        cycles_data = {
            "Préscolaire": ["Préscolaire"],
            "Fondamental": [f"{n}ème AF" for n in range(1, 10)],
            "Secondaire": ["NS1", "NS2", "NS3", "NS4"],
        }
        levels = {}
        for order, (cycle_name, level_names) in enumerate(cycles_data.items(), start=1):
            cycle, _ = Cycle.objects.get_or_create(name=cycle_name, defaults={"order": order})
            for level_order, level_name in enumerate(level_names, start=1):
                level, _ = Level.objects.get_or_create(
                    name=level_name, cycle=cycle, defaults={"order": level_order}
                )
                levels[level_name] = level

        subjects_data = [
            ("Mathématiques", "MATH"), ("Français", "FR"), ("Créole", "KRE"),
            ("Sciences Expérimentales", "SCI"), ("Sciences Sociales", "SOC"),
            ("Anglais", "ANG"),
        ]
        subjects = {}
        for name, code in subjects_data:
            subject, _ = Subject.objects.get_or_create(name=name, defaults={"code": code})
            subjects[name] = subject

        periods = []
        for order in range(1, 4):
            period, _ = Period.objects.get_or_create(
                school_year=year, name=f"Trimestre {order}", defaults={"order": order}
            )
            periods.append(period)

        classrooms = []
        for level_name in ["6ème AF", "9ème AF", "NS2"]:
            level = levels[level_name]
            classroom, _ = ClassRoom.objects.get_or_create(
                school_year=year, level=level, section="A",
                defaults={"main_teacher": teacher_users[0][1] if level_name == "NS2" else None},
            )
            classrooms.append(classroom)

        for classroom in classrooms:
            for name, _ in subjects_data:
                ClassSubject.objects.get_or_create(
                    classroom=classroom, subject=subjects[name],
                    defaults={"teacher": teacher_users[0][1], "coefficient": random.choice([1, 2, 3]),
                              "weekly_hours": 2},
                )

        students_data = [
            ("Nadège", "Michel", "F", 0), ("Wilner", "Étienne", "M", 0),
            ("Sandra", "Cadeau", "F", 1), ("Ronaldo", "Simon", "M", 1),
            ("Daphnée", "Élisée", "F", 2),
        ]
        students = []
        for i, (first, last, gender, classroom_idx) in enumerate(students_data, start=1):
            student, _ = Student.objects.get_or_create(
                matricule=f"ELV-2026-{i:03d}",
                defaults={"first_name": first, "last_name": last, "gender": gender,
                          "classroom": classrooms[classroom_idx], "status": "ACTIF",
                          "birth_date": date(2010 + i, 3, 15)},
            )
            students.append(student)

        parent_user, created = User.objects.get_or_create(
            username="parent1",
            defaults={"role": User.Role.PARENT, "first_name": "Josué", "last_name": "Michel"},
        )
        if created:
            parent_user.set_password("Parent2026!")
            parent_user.save()
        parent, _ = Parent.objects.get_or_create(
            first_name="Josué", last_name="Michel",
            defaults={"user": parent_user, "relation": "PERE", "phone": "+509 3712 0000"},
        )
        ParentStudent.objects.get_or_create(parent=parent, student=students[0], defaults={"is_primary": True})

        eleve_user, created = User.objects.get_or_create(
            username="eleve1",
            defaults={"role": User.Role.ELEVE, "first_name": students[0].first_name,
                      "last_name": students[0].last_name},
        )
        if created:
            eleve_user.set_password("Eleve2026!")
            eleve_user.save()
        students[0].user = eleve_user
        students[0].save(update_fields=["user"])

        for cs in ClassSubject.objects.all():
            for student in students:
                if student.classroom != cs.classroom:
                    continue
                for period in periods:
                    existing = Grade.objects.filter(student=student, class_subject=cs, period=period)
                    if existing.exists():
                        continue
                    Grade.objects.create(
                        student=student, class_subject=cs, period=period,
                        kind=random.choice(["DEVOIR", "CONTROLE", "EXAMEN"]),
                        score=round(random.uniform(8, 19), 2), entered_by=teacher_users[0][0],
                    )

        today = date.today()
        for student in students:
            for offset in range(10):
                day = today - timedelta(days=offset)
                AttendanceRecord.objects.get_or_create(
                    student=student, date=day,
                    defaults={"status": random.choices(["PRESENT", "ABSENT", "RETARD"], [8, 1, 1])[0]},
                )

        fee, _ = FeeType.objects.get_or_create(
            name="Frais de scolarité", school_year=year,
            defaults={"amount": 12000, "description": "Frais mensuels"},
        )
        for student in students:
            invoice, _ = Invoice.objects.get_or_create(
                student=student, fee_type=fee,
                defaults={"amount": 12000, "due_date": today + timedelta(days=15)},
            )
            if not invoice.payments.exists() and random.random() < 0.6:
                Payment.objects.create(
                    invoice=invoice, amount=6000, method="MONCASH",
                    reference="DEMO-001", received_by=direction,
                )

        self.stdout.write(self.style.SUCCESS(
            "Données SIGES créées. Comptes : admin/AdminLNFCL2026!, direction/Direction2026!, "
            "prof1/Prof2026!, eleve1/Eleve2026!, parent1/Parent2026!"
        ))
