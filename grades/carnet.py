"""Preparasyon done karn\u00e8 a \u2014 pataje ant paj HTML ak PDF (ReportLab).

Tout kalkil yo s\u00e8vi ak menm mod\u00e8l Grade ki deja genyen:
subject_average / general_average / koefisyan ClassSubject.
"""
from django.db.models import Avg

from .models import Grade

CYCLE_LABELS = [
    "1er cycle", "2e cycle", "3e cycle", "4e cycle", "5e cycle", "6e cycle",
]


def is_official_level(level_name):
    lvl = "".join(str(level_name or "").lower().split()).replace(".", "")
    return "ns4" in lvl or lvl[:2] in ("9e", "9\u00e8")


def _decision(avg):
    if avg is None:
        return "Pa gen n\u00f2t"
    if avg >= 10:
        return "ADMIS"
    if avg >= 8:
        return "ADMIS \u2014 AV\u00c8TISMAN"
    return "REDOUBLE"


def _mention(avg):
    if avg is None:
        return "\u2014"
    if avg >= 16:
        return "Tr\u00e8s Bien"
    if avg >= 14:
        return "Bien"
    if avg >= 12:
        return "Assez Bien"
    if avg >= 10:
        return "Passable"
    if avg >= 8:
        return "Faible"
    return "Insuffisant"


def _annual_from_periods(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def build_carnet(student):
    """Retounen tout done karnè a pou yon elèv (manadjè HTML + PDF)."""
    classroom = student.classroom
    result = {
        "student": student,
        "classroom": classroom,
        "periods": [],
        "table": {"rows": [], "total_coef": 0, "total_points": None,
                  "classe_annual": None},
        "per_period": [],   # {period, moy, class_moy, rank, out_of, decision}
        "annual_moy": None,
        "annual_decision": None,
        "annual_mention": None,
        "annual_rank": None,
        "annual_out_of": 0,
        "is_official": False,
        "officials": [],
        "chart_labels": [],
        "chart_data": [],
    }
    if not classroom:
        return result

    school_year = classroom.school_year
    periods = list(school_year.periods.order_by("order"))
    result["periods"] = periods
    subjects = list(
        classroom.subjects.select_related("subject", "teacher", "teacher__user").order_by("subject__name")
    )

    rows = []
    total_coef = 0
    total_points = 0.0
    cl_points = 0.0
    cl_coef = 0
    for cs in subjects:
        avgs = []
        for p in periods:
            avg = Grade.subject_average(student, cs, p)
            avgs.append(round(float(avg), 2) if avg is not None else None)
        moy = _annual_from_periods(avgs)
        if moy is not None:
            total_points += moy * cs.coefficient
            total_coef += cs.coefficient
        cls_avgs = []
        cl_moy = None
        for p in periods:
            a = Grade.objects.filter(class_subject=cs, period=p).aggregate(a=Avg("score"))["a"]
            cls_avgs.append(round(float(a), 2) if a is not None else None)
        cl_moy = _annual_from_periods(cls_avgs)
        if cl_moy is not None:
            cl_points += cl_moy * cs.coefficient
            cl_coef += cs.coefficient
        rows.append({
            "cs": cs,
            "subject_name": cs.subject.name,
            "coef": cs.coefficient,
            "avgs": avgs,
            "moy": moy,
            "teacher": str(cs.teacher) if cs.teacher else "\u2014",
            "cls_avgs": cls_avgs,
            "cls_moy": cl_moy,
        })
    result["table"]["rows"] = rows
    result["table"]["total_coef"] = total_coef
    result["table"]["total_points"] = round(total_points, 2) if total_coef else None
    result["table"]["classe_annual"] = round(cl_points / cl_coef, 2) if cl_coef else None

    per_period = []
    for i, p in enumerate(periods):
        moy_i = Grade.general_average(student, p)
        cl_gen = None
        pc = pcoef = 0
        for cs in subjects:
            a = Grade.objects.filter(class_subject=cs, period=p).aggregate(a=Avg("score"))["a"]
            if a is not None:
                pc += float(a) * cs.coefficient
                pcoef += cs.coefficient
        if pcoef:
            cl_gen = round(pc / pcoef, 2)
        rank, out_of = None, 0
        ranking = Grade.class_ranking(classroom, p)
        out_of = len(ranking)
        for r, s, a in ranking:
            if s.pk == student.pk:
                rank = r
                break
        from .views import _decision as decision_of
        dec, _tone = decision_of(moy_i)
        per_period.append({
            "period": p,
            "label": CYCLE_LABELS[i] if i < len(CYCLE_LABELS) else p.name,
            "cycle_label": CYCLE_LABELS[i] + f" ({p.name})" if i < len(CYCLE_LABELS) else p.name,
            "moy": moy_i,
            "class_moy": cl_gen,
            "rank": rank,
            "out_of": out_of,
            "decision": dec,
        })
    result["per_period"] = per_period

    annual = _annual_from_periods([pp["moy"] for pp in per_period])
    result["annual_moy"] = annual
    result["annual_decision"] = _decision(annual)
    result["annual_mention"] = _mention(annual)
    if annual is not None:
        ranks = []
        for st in classroom.students.filter(status="ACTIF"):
            a = _annual_from_periods([Grade.general_average(st, p) for p in periods])
            if a is not None:
                ranks.append((a, st))
        ranks.sort(key=lambda t: (-t[0], t[1].last_name, t[1].first_name))
        result["annual_out_of"] = len(ranks)
        for r, (a, st) in enumerate(ranks, start=1):
            if st.pk == student.pk:
                result["annual_rank"] = r
                break

    result["is_official"] = is_official_level(classroom.level.name)
    if result["is_official"]:
        for row in rows:
            g = Grade.latest_exam(student, row["cs"])
            score = g.score if g else None
            result["officials"].append({
                "cs": row["cs"],
                "subject_name": row["subject_name"],
                "score": score,
                "teacher": row["teacher"],
            })
            if score is not None:
                result["chart_labels"].append(row["subject_name"])
                result["chart_data"].append(float(score))
    return result


# ============ Imposition livret (pli A4 landscape \u2192 A5) ============

def livret_sides(pages):
    """Re organising an es\u00e8y pou enpresyon livre: retounen lis 'c\u00f4t\u00e9', chak = 2 paj (goch, dwat).

    pages = lis paj (1 = kouv\u00e8ti devan, N = kouv\u00e8ti d\u00e8y\u00e8). N ranpli otomatikman an bl
    pou rive yon miltip de 4.
    """
    n = len(pages)
    if n % 4:
        blanks = 4 - (n % 4)
        pages = list(pages) + [None] * blanks
    n = len(pages)
    sides = []
    lo, hi = 0, n - 1
    while lo <= hi:
        if lo == hi:
            sides.append([pages[lo], None])
            break
        sides.append([pages[hi], pages[lo]])
        sides.append([pages[lo + 1], pages[hi - 1]])
        lo += 2
        hi -= 2
    return sides


def build_html_pages(data, max_rows=14):
    """Lis paj HTML karn\u00e8 a (menm estrikti ak pdf.build_pages pou imposition livret)."""
    pages = [
        {"kind": "cover"},
        {"kind": "reglement"},
        {"kind": "identification"},
    ]
    rows = data["table"]["rows"]
    if rows:
        chunks = [rows[i:i + max_rows] for i in range(0, len(rows), max_rows)]
        for idx, chunk in enumerate(chunks, start=1):
            pages.append({
                "kind": "notes",
                "chunk": chunk,
                "part": idx,
                "nparts": len(chunks),
                "with_totals": idx == len(chunks),
            })
    pages.append({"kind": "results"})
    if data["is_official"]:
        pages.append({"kind": "officiel"})
    pages.append({"kind": "observations"})
    pages.append({"kind": "back"})
    return pages


def html_sides(pages):
    """Entepozisyon livret pou mod\u00e8l HTML la: lis {no, recto, left, right}."""
    padded = list(pages)
    while len(padded) % 4:
        padded.append({"kind": "blank"})
    sides = []
    for i, (lo_idx, hi_idx) in enumerate(livret_sides(list(range(len(padded))))):
        sides.append({
            "no": i + 1,
            "recto": i % 2 == 0,
            "left": padded[lo_idx] if lo_idx is not None else None,
            "right": padded[hi_idx] if hi_idx is not None else None,
        })
    return sides
