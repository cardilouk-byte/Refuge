from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.views import teaching_staff_required as staff_required
from academics.models import ClassRoom, Period

from . import exports, imports


def _xlsx_response(wb, filename):
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@staff_required
def index(request):
    classrooms = ClassRoom.objects.select_related("level", "school_year")
    periods = Period.objects.select_related("school_year")
    return render(request, "excel_manager/index.html", {
        "classrooms": classrooms,
        "periods": periods,
    })


@staff_required
def export_students(request):
    classroom_id = request.GET.get("classe")
    classroom = ClassRoom.objects.filter(pk=classroom_id).first() if classroom_id else None
    wb = exports.students_workbook(classroom)
    name = f"eleves_{classroom.name.replace(' ', '_')}.xlsx" if classroom else "eleves.xlsx"
    return _xlsx_response(wb, name)


@staff_required
def template_students(request):
    return _xlsx_response(exports.students_template(), "modele_eleves.xlsx")


@staff_required
def template_grades(request):
    classroom = ClassRoom.objects.filter(pk=request.GET.get("classe")).first()
    if classroom is None:
        messages.error(request, "Choisissez une classe.")
        return redirect("excel_manager:index")
    return _xlsx_response(exports.grades_template(classroom),
                          f"modele_notes_{classroom.name.replace(' ', '_')}.xlsx")


@staff_required
def export_grades(request):
    classroom = ClassRoom.objects.filter(pk=request.GET.get("classe")).first()
    period = Period.objects.filter(pk=request.GET.get("periode")).first()
    if classroom is None or period is None:
        messages.error(request, "Choisissez une classe et une période.")
        return redirect("excel_manager:index")
    wb = exports.grades_grid(classroom, period)
    return _xlsx_response(wb,
                          f"notes_{classroom.name.replace(' ', '_')}_{period.name.replace(' ', '_')}.xlsx")


@staff_required
def import_students_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        result = imports.import_students(request.FILES["file"])
        if result["errors"]:
            messages.warning(request,
                             f"{result['created']} créés, {result['updated']} mis à jour, "
                             f"{len(result['errors'])} erreur(s).")
        else:
            messages.success(request,
                             f"Import réussi : {result['created']} créés, {result['updated']} mis à jour.")
        return render(request, "excel_manager/import_result.html", {
            "result": result, "kind": "élèves",
        })
    return redirect("excel_manager:index")


@staff_required
def import_grades_view(request):
    classroom = ClassRoom.objects.filter(pk=request.POST.get("classe")).first()
    period = Period.objects.filter(pk=request.POST.get("periode")).first()
    if classroom is None or period is None:
        messages.error(request, "Choisissez une classe et une période.")
        return redirect("excel_manager:index")
    if request.FILES.get("file"):
        result = imports.import_grades(request.FILES["file"], classroom, period, request.user)
        if result["errors"]:
            messages.warning(request, f"{result['created']} notes importées, "
                                      f"{len(result['errors'])} erreur(s).")
        else:
            messages.success(request, f"Import réussi : {result['created']} notes enregistrées.")
        return render(request, "excel_manager/import_result.html", {
            "result": result, "kind": "notes",
        })
    return redirect("excel_manager:index")
