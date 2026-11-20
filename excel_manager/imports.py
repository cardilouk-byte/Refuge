from datetime import date, datetime

from openpyxl import load_workbook

from academics.models import ClassRoom, ClassSubject
from grades.models import Grade
from students.models import Student


def _cell(row, index):
    value = row[index - 1] if index <= len(row) else None
    if value is None:
        return ""
    return str(value).strip()


def import_students(xlsx_file):
    wb = load_workbook(xlsx_file, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    created, updated, errors = 0, 0, []

    for line, row in enumerate(rows, start=2):
        matricule = _cell(row, 1)
        first_name = _cell(row, 2)
        last_name = _cell(row, 3)
        if not matricule and not first_name and not last_name:
            continue
        if not matricule or not first_name or not last_name:
            errors.append({"line": line, "error": "Matricule, prénom et nom sont obligatoires."})
            continue

        gender = _cell(row, 4).upper()[:1]
        if gender not in ("M", "F"):
            gender = ""
        birth_raw = row[4] if len(row) >= 5 else None
        birth_date = None
        if birth_raw:
            try:
                if isinstance(birth_raw, datetime):
                    birth_date = birth_raw.date()
                else:
                    birth_date = date.fromisoformat(str(birth_raw).strip())
            except ValueError:
                errors.append({"line": line, "error": f"Date de naissance invalide : {birth_raw}"})
                continue

        classroom = None
        classroom_name = _cell(row, 9)
        if classroom_name:
            parts = classroom_name.rsplit(" ", 1)
            if len(parts) == 2:
                classroom = ClassRoom.objects.filter(
                    level__name=parts[0], section=parts[1]
                ).first()
            if classroom is None:
                errors.append({"line": line, "error": f"Classe introuvable : {classroom_name}"})
                continue

        student, was_created = Student.objects.update_or_create(
            matricule=matricule,
            defaults={
                "first_name": first_name, "last_name": last_name, "gender": gender,
                "birth_date": birth_date, "nis": _cell(row, 6), "ninu": _cell(row, 7),
                "address": _cell(row, 8), "classroom": classroom,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
    return {"created": created, "updated": updated, "errors": errors}


def import_grades(xlsx_file, classroom, period, user):
    wb = load_workbook(xlsx_file, data_only=True)
    ws = wb.active
    header_row = [str(c).strip() if c else "" for c in
                  next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    subject_map = {}
    for index, title in enumerate(header_row, start=1):
        if index <= 2 or not title:
            continue
        subject_name = title.split("(")[0].strip()
        cs = classroom.subjects.filter(subject__name__iexact=subject_name).first()
        if cs is None:
            cs = ClassSubject.objects.filter(
                classroom=classroom, subject__name__icontains=subject_name
            ).first() or classroom.subjects.filter(subject__code__iexact=subject_name).first()
        if cs:
            subject_map[index] = cs

    created, errors = 0, []
    for line, row in enumerate(rows, start=2):
        matricule = _cell(row, 1)
        if not matricule:
            continue
        student = Student.objects.filter(matricule=matricule).first()
        if student is None:
            errors.append({"line": line, "error": f"Élève introuvable : {matricule}"})
            continue
        if student.classroom != classroom:
            errors.append({"line": line,
                           "error": f"{student.full_name} n'est pas dans {classroom.name}"})
            continue
        for index, cs in subject_map.items():
            raw = row[index - 1] if index <= len(row) else None
            if raw in (None, ""):
                continue
            try:
                score = float(str(raw).replace(",", "."))
            except ValueError:
                errors.append({"line": line,
                               "error": f"Note invalide ({raw}) pour {cs.subject.name}"})
                continue
            if not 0 <= score <= 20:
                errors.append({"line": line,
                               "error": f"Note hors barème 0-20 ({score}) pour {cs.subject.name}"})
                continue
            Grade.objects.create(
                student=student, class_subject=cs, period=period,
                kind="EXAMEN", score=score, entered_by=user,
            )
            created += 1
    return {"created": created, "errors": errors}
