"""API deviz SIGES \u2014 100% gratis, san token.

Sekirit\u00e9:
- /api/ping/ : piblik (cont\u00e8 sante s\u00e8vis la s\u00e8lman).
- L\u00f2t toutGET : f\u00e2t loge epi p\u00e8son\u00e8l lek\u00f2l (is_staff / SUPERADMIN / DIRECTION / ENSEIGNANT).
- Lekti s\u00e8lman \u2014 pa gen ekriti, pa gen done prive (mway\u00e8n + stats agreg\u00e8).
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

User = get_user_model()

STAFF_ROLES = (User.Role.SUPERADMIN, User.Role.DIRECTION, User.Role.ENSEIGNANT)
API_VERSION = "1.0"


def _num(v):
    """Decimal \u2192 float (2 chif), None lak\u00e8z None."""
    return round(float(v), 2) if v is not None else None


def _staff_api(request):
    u = request.user
    if not u.is_authenticated:
        raise PermissionDenied("F\u00e2t loge pou s\u00e8vi ak API a.")
    if not (u.is_staff or u.role in STAFF_ROLES):
        raise PermissionDenied("S\u00e8lman p\u00e8son\u00e8l lek\u00f2l la gen aks\u00e8 API a.")


@require_GET
def ping(request):
    return JsonResponse({
        "ok": True,
        "service": "LNFCL SIGES API",
        "versyon": API_VERSION,
        "dat": timezone.localtime().strftime("%Y-%m-%d"),
        "l\u00e8": timezone.localtime().strftime("%H:%M"),
        "loge": bool(request.user.is_authenticated),
    })


@require_GET
def docs(request):
    _staff_api(request)
    return render(request, "api/docs.html", {"titre": "API SIGES"})


@require_GET
def stats(request):
    _staff_api(request)
    from academics.models import ClassRoom, Cycle, Level, Period, SchoolYear
    from finance.models import Expense, Invoice
    from students.models import Parent, Student
    from teachers.models import Teacher

    year = SchoolYear.objects.filter(is_current=True).first()
    invoices_unpaid = Invoice.objects.exclude(status=Invoice.Status.PAYE)
    return JsonResponse({
        "anne_kouran": year.label if year else None,
        "tota": {
            "el\u00e8v": Student.objects.count(),
            "el\u00e8v_aktif": Student.objects.filter(status="ACTIF").count(),
            "pwofes\u00e8": Teacher.objects.count(),
            "paran": Parent.objects.count(),
            "klas": ClassRoom.objects.count(),
            "nivo": Level.objects.count(),
            "syik": Cycle.objects.count(),
            "p\u00e9ry\u00f2d": Period.objects.count(),
        },
        "efektif_pa_syik": [
            {"syik": c.name, "el\u00e8v": Student.objects.filter(classroom__level__cycle=c).count()}
            for c in Cycle.objects.order_by("order")
        ],
        "finans": {
            "vani_fakti_tot": _num(Invoice.objects.aggregate(s=Sum("amount"))["s"]),
            "peye": _num(Invoice.objects.filter(status=Invoice.Status.PAYE)
                         .aggregate(s=Sum("amount"))["s"]),
            "dettes": _num(invoices_unpaid.aggregate(s=Sum("amount"))["s"]),
            "fakti_poko_peye": invoices_unpaid.count(),
            "depans": _num(Expense.objects.aggregate(s=Sum("amount"))["s"]),
        },
    })


@require_GET
def nivo(request):
    _staff_api(request)
    from academics.models import Cycle

    data = []
    for c in Cycle.objects.order_by("order"):
        data.append({
            "syik": c.name,
            "l\u00f2d": c.order,
            "nivo": [{"id": l.pk, "non": l.name, "l\u00f2d": l.order}
                     for l in c.levels.order_by("order")],
        })
    return JsonResponse({"syik": data})


@require_GET
def matye(request):
    _staff_api(request)
    from academics.models import Subject

    return JsonResponse({"matye": [{
        "id": s.pk, "non": s.name, "k\u00f2d": s.code,
        "klas_kap_mache_l": s.class_assignments.count(),
    } for s in Subject.objects.order_by("name")]})


@require_GET
def klas(request):
    _staff_api(request)
    from academics.models import ClassRoom

    data = []
    for cr in ClassRoom.objects.select_related("level__cycle", "school_year"):
        data.append({
            "id": cr.pk, "non": cr.name,
            "nivo": cr.level.name,
            "syik": cr.level.cycle.name,
            "ane": cr.school_year.label,
            "seksyon": cr.section,
            "el\u00e8v": cr.students.count(),
            "matye": [{"non": cs.subject.name, "koef": cs.coefficient, "pwofes\u00e8": cr_str(cs.teacher)}
                      for cs in cr.subjects.select_related("subject", "teacher")],
        })
    return JsonResponse({"klas": data})


def cr_str(teacher):
    return teacher.full_name if teacher else None


@require_GET
def elev(request, matricule):
    _staff_api(request)
    from academics.models import Period
    from finance.models import Invoice
    from grades.models import Grade
    from students.models import Student

    st = Student.objects.filter(matricule=matricule).select_related(
        "classroom__level__cycle", "classroom__school_year").first()
    if not st:
        return JsonResponse({"er\u00e8": "el\u00e8v sa a pa egziste"}, status=404)
    cr = st.classroom
    per_period = []
    for p in Period.objects.filter(school_year=cr.school_year).order_by("order") if cr else []:
        per_period.append({
            "p\u00e9ry\u00f2d": p.name,
            "moyen_j\u00e9neral": _num(Grade.general_average(st, p)),
        })
    inv = list(Invoice.objects.filter(student=st))
    return JsonResponse({
        "matricule": st.matricule,
        "non": st.last_name, "pwemye_non": st.first_name,
        "klas": cr.name if cr else None,
        "nivo": cr.level.name if cr else None,
        "syik": cr.level.cycle.name if cr else None,
        "anne": cr.school_year.label if cr else None,
        "status": st.status,
        "moyen_pa_p\u00e9ry\u00f2d": per_period,
        "peman": [{"id": i.pk, "tip_f\u00e8": i.fee_type.name, "mo": _num(i.amount),
                   "peye": _num(i.paid_amount), "status": i.status} for i in inv],
        "tout_f\u00e8_peye": bool(inv) and all(i.status == Invoice.Status.PAYE for i in inv),
    })


@require_GET
def bulletin(request, matricule):
    _staff_api(request)
    from academics.models import ClassSubject, Period
    from grades.models import Grade
    from students.models import Student

    st = Student.objects.filter(matricule=matricule).select_related("classroom__level__cycle").first()
    if not st:
        return JsonResponse({"er\u00e8": "el\u00e8v sa a pa egziste"}, status=404)
    cr = st.classroom
    if not cr:
        return JsonResponse({"er\u00e8": "el\u00e8v la pa gen klas"}, status=404)
    data = []
    for p in Period.objects.filter(school_year=cr.school_year).order_by("order"):
        rows = []
        for cs in cr.subjects.select_related("subject", "teacher").order_by("subject__name"):
            rows.append({
                "matye": cs.subject.name,
                "koef": cs.coefficient,
                "moyen": _num(Grade.subject_average(st, cs, p)),
                "pwofes\u00e8": cr_str(cs.teacher),
            })
        rank, out_of = None, None
        for r, s_row, _avg in Grade.class_ranking(cr, p):
            if s_row.pk == st.pk:
                rank, out_of = r, len([1 for _r, _s, a in Grade.class_ranking(cr, p) if a is not None])
                break
        data.append({
            "p\u00e9ry\u00f2d": p.name,
            "moyen_j\u00e9neral": _num(Grade.general_average(st, p)),
            "plas": rank,
            "sou": out_of,
            "line": rows,
        })
    return JsonResponse({"el\u00e8v": st.full_name, "klas": cr.name, "bulletin": data})
