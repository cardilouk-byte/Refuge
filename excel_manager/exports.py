from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from grades.models import Grade

HEADER_FILL = PatternFill("solid", fgColor="0D6EFD")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _style_header(ws, headers):
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col)].width = 22


def students_workbook(classroom=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "Élèves"
    headers = ["Matricule", "Prénom", "Nom", "Sexe (M/F)", "Date naissance (AAAA-MM-JJ)",
               "NIS", "NINU", "Adresse", "Classe"]
    _style_header(ws, headers)
    students = __import__("students").models.Student.objects.select_related(
        "classroom").order_by("classroom", "last_name")
    if classroom:
        students = students.filter(classroom=classroom)
    for row, student in enumerate(students, start=2):
        ws.cell(row=row, column=1, value=student.matricule)
        ws.cell(row=row, column=2, value=student.first_name)
        ws.cell(row=row, column=3, value=student.last_name)
        ws.cell(row=row, column=4, value=student.gender)
        ws.cell(row=row, column=5, value=student.birth_date.isoformat() if student.birth_date else "")
        ws.cell(row=row, column=6, value=student.nis)
        ws.cell(row=row, column=7, value=student.ninu)
        ws.cell(row=row, column=8, value=student.address)
        ws.cell(row=row, column=9, value=student.classroom.name if student.classroom else "")
    return wb


def students_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Élèves"
    headers = ["Matricule", "Prénom", "Nom", "Sexe (M/F)", "Date naissance (AAAA-MM-JJ)",
               "NIS", "NINU", "Adresse", "Classe"]
    _style_header(ws, headers)
    for row in range(2, 12):
        ws.cell(row=row, column=1, value=f"ELV-EX-{row - 1:03d}")
    return wb


def grades_template(classroom):
    wb = Workbook()
    ws = wb.active
    ws.title = "Notes"
    class_subjects = classroom.subjects.select_related("subject").order_by("subject__name")
    headers = ["Matricule", "Nom complet"]
    for cs in class_subjects:
        headers.append(f"{cs.subject.name}" + (f" ({cs.subject.code})" if cs.subject.code else ""))
    _style_header(ws, headers)
    for row, student in enumerate(classroom.students.filter(status="ACTIF"), start=2):
        ws.cell(row=row, column=1, value=student.matricule)
        ws.cell(row=row, column=2, value=student.full_name)
    ws.freeze_panes = "C2"
    return wb


def grades_grid(classroom, period):
    wb = Workbook()
    ws = wb.active
    ws.title = "Notes"
    class_subjects = list(classroom.subjects.select_related("subject").order_by("subject__name"))
    headers = ["Matricule", "Nom complet"]
    for cs in class_subjects:
        headers.append(f"{cs.subject.name}")
    headers.append("Moyenne générale")
    _style_header(ws, headers)
    for row, student in enumerate(classroom.students.filter(status="ACTIF"), start=2):
        ws.cell(row=row, column=1, value=student.matricule)
        ws.cell(row=row, column=2, value=student.full_name)
        col = 3
        points, coefs = 0.0, 0
        for cs in class_subjects:
            avg = Grade.subject_average(student, cs, period)
            avg_value = round(float(avg), 2) if avg is not None else None
            ws.cell(row=row, column=col, value=avg_value)
            if avg_value is not None:
                points += avg_value * cs.coefficient
                coefs += cs.coefficient
            col += 1
        general = round(points / coefs, 2) if coefs else None
        ws.cell(row=row, column=col, value=general)
    ws.freeze_panes = "C2"
    return wb
