"""Jenere karn\u00e8 lek\u00f2l la an PDF ak ReportLab \u2014 vr\u00e8 livret A5.

De m\u00f2d:
- ``lekti`` : paj A5 portrait nan l\u00f2d n\u00e8mal (1 = kouv\u00e8ti devan \u2192 N = kouv\u00e8ti d\u00e8y\u00e8).
- ``livret`` : entepozisyon pou enpresyon reto-v\u00e8so: chak paj fizik A4
  landscape genyen 2 paj A5 (goch/dwat) ki pare pou pli.

Pa gen f\u00f2mil kalkil: tout n\u00f2t/koef/mway\u00e8n s\u00f2ti nan `grades.carnet.build_carnet`
(mod\u00e8l Grade/ClassSubject ki deja egziste).
"""
import io
import os

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5, A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Table, TableStyle, Paragraph

from .carnet import livret_sides

A5W, A5H = A5  # 419.5 x 595.3 (portrait)
A4LW, A4LH = landscape(A4)  # 841.9 x 595.3
M = 22  # maj ak b\u00f2 an mmm (pt)
INK = colors.HexColor("#1a1a1a")
LINE = colors.HexColor("#333333")
HEAD_BG = colors.HexColor("#eef1f6")


class CarnetRenderer:
    def __init__(self, data, carnet, site):
        """data = `grades.carnet.build_carnet(student)`; carnet = CarnetSettings; site = SiteSettings."""
        self.d = data
        self.carnet = carnet
        self.site = site
        self.border = colors.HexColor(getattr(carnet, "border_color", "#1f2937") or "#1f2937")
        self.page_no = 0
        self.logo_path = self._media_path(getattr(site, "logo", None))
        self.photo_path = (
            self._media_path(getattr(data["student"], "photo", None))
            if getattr(carnet, "show_photo", True)
            else None
        )

    # ---------- helpers ----------
    @staticmethod
    def _media_path(field_file):
        name = getattr(field_file, "name", None)
        if not name:
            return None
        path = os.path.join(settings.MEDIA_ROOT, name)
        return path if os.path.exists(path) else None

    def _std_header(self, c, w, h):
        car = self.carnet
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(w / 2, h - 30, car.school_name)
        c.setFont("Helvetica", 6.5)
        meta = car.address
        tels = " / ".join(t for t in (car.tel1, car.tel2) if t)
        if tels:
            meta += "  \u2014  " + tels
        if car.email:
            meta += "  \u2014  " + car.email
        c.drawCentredString(w / 2, h - 39, meta[:110])

    def _frame(self, c, w, h):
        c.setStrokeColor(self.border)
        c.setLineWidth(1.4)
        c.rect(M - 8, M - 8, w - 2 * (M - 8), h - 2 * (M - 8))
        c.setLineWidth(0.5)
        c.rect(M - 5, M - 5, w - 2 * (M - 5), h - 2 * (M - 5))

    def _footer(self, c, w):
        self.page_no += 1
        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(colors.HexColor("#445566"))
        c.drawCentredString(w / 2, 24, self.carnet.footer_motto)
        c.setFont("Helvetica", 6)
        c.drawRightString(w - M, 24, f"p. {self.page_no}")
        c.setFillColor(INK)

    def _sig_line(self, c, x, y, label):
        c.setFont("Helvetica", 7)
        c.drawString(x, y, label + " : .....................")

    def _cachet(self, c, x, y):
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.circle(x, y, 30)
        c.setFont("Helvetica-Oblique", 5.5)
        c.drawCentredString(x, y - 2, "Cachet de")
        c.drawCentredString(x, y - 10, "l'\u00e9tablissement")

    def _stamp_unpaid(self, c, w, h):
        """Filigran wouj sou chak paj lè elèv la poko peye."""
        c.saveState()
        c.translate(w / 2, h / 2)
        c.rotate(26)
        c.setFillColor(colors.Color(0.85, 0.12, 0.12, alpha=0.13))
        c.setFont("Helvetica-Bold", 44)
        c.drawCentredString(0, 10, "NON VALIDÉ")
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(0, -24, "Peman poko fèt — karnè paka valide")
        c.restoreState()

    def _cycle_badge(self, c, w, h, paid):
        """Piti badge sou chak fèy nòt — valiad syik pa syik selon peman an."""
        txt = "SYIK VALIDE" if paid else "SYIK PAKA VALIDE"
        col = colors.HexColor("#198754") if paid else colors.HexColor("#dc3545")
        bw = 78 if paid else 104
        c.saveState()
        c.setStrokeColor(col)
        c.setLineWidth(0.9)
        c.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=0.10))
        c.roundRect(w - 30 - bw, 34, bw, 16, 3, stroke=1, fill=1)
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(w - 30 - bw / 2, 38, txt)
        c.restoreState()

    def _stamp_valid(self, c, x, y):
        """Kachèt vèt VALIDE — DIRECTION (lè tout fakti yo peye)."""
        c.saveState()
        c.translate(x, y)
        c.rotate(-11)
        c.setStrokeColor(colors.HexColor("#198754"))
        c.setLineWidth(1.4)
        c.rect(-62, -14, 124, 30)
        c.setFillColor(colors.HexColor("#198754"))
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(0, 3, "VALIDÉ — DIRECTION")
        c.setFont("Helvetica", 6)
        c.drawCentredString(0, -7, "Tout fès yo peye — tousyik yo valide")
        c.restoreState()

    def _field(self, c, x, y, label, value, width=170):
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x, y, label + " :")
        c.setFont("Helvetica", 7.5)
        txt = str(value or "")
        c.drawString(x + 8 + c.stringWidth(label + " : ", "Helvetica-Bold", 7.5), y, txt[:60])
        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(x, y - 3, x + width, y - 3)

    def _img(self, c, path, x, y, box_w, box_h):
        if not path:
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.rect(x, y, box_w, box_h)
            c.setFont("Helvetica-Oblique", 5.5)
            c.drawCentredString(x + box_w / 2, y + box_h / 2 - 2, "Photo \u00e9l\u00e8ve")
            return
        try:
            img = ImageReader(path)
            iw, ih = img.getSize()
            scale = min(box_w / iw, box_h / ih)
            dw, dh = iw * scale, ih * scale
            c.drawImage(img, x + (box_w - dw) / 2, y + (box_h - dh) / 2, dw, dh)
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.rect(x, y, box_w, box_h)
        except Exception:
            self._img(c, None, x, y, box_w, box_h)

    # ---------- paj yo ----------
    def page_cover(self, c, w, h):
        self._frame(c, w, h)
        car = self.carnet
        y = h - 70
        if self.logo_path:
            try:
                img = ImageReader(self.logo_path)
                iw, ih = img.getSize()
                bw = 66
                c.drawImage(img, (w - bw) / 2, y - 50, bw, min(ih * bw / iw, 66))
                y -= 78
            except Exception:
                pass
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 12.5)
        c.drawCentredString(w / 2, y, car.school_name)
        y -= 14
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, y, car.slogan.upper())
        y -= 11
        c.setFont("Helvetica", 6.5)
        meta = car.address
        tels = " / ".join(t for t in (car.tel1, car.tel2) if t)
        if tels:
            meta += " \u2014 T\u00e9ls: " + tels
        if car.email:
            meta += " \u2014 " + car.email
        c.drawCentredString(w / 2, y, meta[:110])
        y -= 26
        c.setStrokeColor(LINE)
        c.line(w / 2 - 60, y, w / 2 + 60, y)
        y -= 24
        classroom = self.d["classroom"]
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w / 2, y, car.subtitle.upper())
        y -= 14
        c.setFont("Helvetica", 8)
        if classroom:
            c.drawCentredString(w / 2, y, classroom.level.cycle.name)
        y -= 4

        # idantifikasyon
        y -= 34
        student = self.d["student"]
        if self.photo_path:
            self._img(c, self.photo_path, w / 2 + 92, y - 22, 74, 92)
        for label, value in (
            ("Nom", student.last_name),
            ("Pr\u00e9nom", student.first_name),
            ("Classe", classroom.name if classroom else ""),
            ("Code (\u00e9tudiant)", student.matricule),
            ("Ann\u00e9e Acad\u00e9mique", classroom.school_year.label if classroom else ""),
        ):
            c.setFont("Helvetica-Bold", 8)
            c.drawString(w / 2 - 105, y, label + " :")
            c.setStrokeColor(LINE)
            c.setLineWidth(0.5)
            c.line(w / 2 - 30, y - 3.5, w / 2 + 80, y - 3.5)
            c.setFont("Helvetica", 8)
            c.setFont("Helvetica", 8)
            c.drawCentredString(w / 2 + 25, y, str(value or "")[:34])
            y -= 20
        self._footer(c, w)

    def page_reglement(self, c, w, h):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=10.5, alignment=1, spaceAfter=6)
        body = ParagraphStyle("b", fontName="Helvetica", fontSize=8, leading=15)
        t = Paragraph("Extraits des r\u00e8glements internes", title)
        t.wrapOn(c, w - 2 * M, h)
        t.drawOn(c, M, h - 66)
        c.setStrokeColor(LINE)
        c.line(w / 2 - 60, h - 70, w / 2 + 60, h - 70)
        items = [i.strip() for i in self.carnet.reglements_text.split("\n") if i.strip()]
        rows = [[Paragraph(i.replace("\u2028", "<br/>"), body)] for i in items]
        table = Table(rows, colWidths=[w - 2 * M - 20])
        table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        table.wrapOn(c, w - 2 * M - 20, h)
        table.drawOn(c, M + 10, h - 86 - table._height)
        self._sig_line(c, M, 68, "Le Directeur")
        self._sig_line(c, M + 180, 68, "Le Parent")
        self._footer(c, w)

    def page_identification(self, c, w, h):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        student, classroom = self.d["student"], self.d["classroom"]
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(w / 2, h - 62, self.carnet.subtitle.upper())
        c.setFont("Helvetica", 7)
        c.drawCentredString(w / 2, h - 74, classroom.school_year.label if classroom else "")
        box_x, box_y, box_w, box_h = M + 14, h - 250, w - 2 * M - 28, 160
        c.setStrokeColor(LINE)
        c.setLineWidth(0.9)
        c.rect(box_x, box_y, box_w, box_h)
        y = box_y + box_h - 24
        rows = [
            ("Nom", student.last_name),
            ("Pr\u00e9nom", student.first_name),
            ("Date de naissance", student.birth_date.strftime("%d/%m/%Y") if student.birth_date else "\u2014"),
            ("Sexe", {"M": "Masculin", "F": "F\u00e9minin"}.get(student.gender, "\u2014")),
            ("Classe", classroom.name if classroom else "\u2014"),
            ("Niveau", classroom.level.name if classroom else "\u2014"),
            ("Ann\u00e9e Scolaire", classroom.school_year.label if classroom else "\u2014"),
        ]
        for label, value in rows:
            c.setFont("Helvetica-Bold", 8)
            label_x, val_x = box_x + 14, box_x + 120
            c.drawString(label_x, y, label + " :")
            c.setFont("Helvetica", 8)
            c.drawString(val_x, y, str(value)[:38])
            c.setLineWidth(0.4)
            c.line(val_x, y - 3, box_x + box_w - 14, y - 3)
            y -= 19.5
        if self.photo_path:
            self._img(c, self.photo_path, box_x + box_w - 64, box_y + 10, 52, 64)
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(w / 2, box_y - 16, "Page de garde conserv\u00e9e par l'\u00e9l\u00e8ve \u2014 pri\u00e8 ne pas arracher")
        self._sig_line(c, M + 10, 52, "Le Directeur")
        self._cachet(c, w - 60, 60)
        self._footer(c, w)

    def _notes_table(self, width, rows, periods):
        col_mat, col_coef = 96, 24
        n_p = max(len(periods), 1)
        col_p = 30 if n_p == 4 else 34
        col_moy = 36
        col_prof = max(width - col_mat - col_coef - col_p * n_p - col_moy, 60)
        header = ["MATI\u00c8RES", "COEF"] + [
            p.get("label") for p in periods
        ] + ["Notes Globales", "Professeurs"]
        body = [[r["subject_name"][:30], str(r["coef"])] +
                [(f"{a:.2f}" if a is not None else "\u2014") for a in r["avgs"]] +
                [(f"{r['moy']:.2f}" if r["moy"] is not None else "\u2014"), r["teacher"][:16]]
                for r in rows]
        tab = Table([header] + body, colWidths=[col_mat, col_coef] + [col_p] * n_p + [col_moy, col_prof], repeatRows=1)
        tab.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.3),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.55, LINE),
            ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
            ("ALIGN", (1, 0), (-2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ]))
        return tab

    def page_notes(self, c, w, h, rows, part, nparts, periods, totals):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        student, classroom = self.d["student"], self.d["classroom"]
        c.setFont("Helvetica-Bold", 8)
        c.drawString(M, h - 58, f"{student.last_name} {student.first_name} ({student.matricule})")
        c.setFont("Helvetica", 6.8)
        klass = f"{classroom.name} \u2014 {classroom.school_year.label}" if classroom else ""
        c.drawRightString(w - M, h - 58, klass)
        inner = w - 2 * M
        tab = self._notes_table(inner, rows, periods)
        avail = h - 90 - 70
        shown, rest = self._chunk_rows(rows, avail, periods, inner)
        tab_shown = self._notes_table(inner, shown, periods)
        tab_shown.wrapOn(c, inner, avail)
        top = h - 90
        tab_shown.drawOn(c, M, top - tab_shown._height)
        y = top - tab_shown._height - 14
        if totals is not None and shown and not rest:
            self._totals_block(c, M, y, inner, totals)
        if rest or part < nparts:
            c.setFont("Helvetica-Oblique", 6.5)
            c.drawString(M, y - 10, f"Tableau suite \u00e0 la page suivante\u2026" if rest else f"Tableau ({part}/{nparts})")
        self._footer(c, w)

    def _chunk_num(self, rows):
        return rows

    def _chunk_rows(self, rows, avail, periods, inner):
        """Split rows so the table fits `avail` pt height (approx 13.5pt/row)."""
        row_h = 13.5
        max_rows = max(int((avail - 16) / row_h), 4)
        return rows[:max_rows], rows[max_rows:]

    def _totals_block(self, c, x, y, w, totals):
        rows = [
            ["Total des coefficients", str(totals["total_coef"])],
            ["Total des points", f"{totals['total_points']:.2f}" if totals["total_points"] is not None else "\u2014"],
            ["Moyenne de l'\u00e9l\u00e8ve", f"{totals['moy']:.2f} /20" if totals["moy"] is not None else "\u2014"],
            ["Moyenne de la classe", f"{totals['classe']:.2f} /20" if totals["classe"] is not None else "\u2014"],
            ["Rang", (f"{totals['rank']}e sur {totals['out_of']}" if totals["rank"] and totals["rank"] != 1 else (f"{totals['rank']}re sur {totals['out_of']}" if totals['rank'] else "\u2014"))],
            ["Mention", totals["mention"]],
            ["D\u00e9cision de fin d'ann\u00e9e", totals["decision"]],
        ]
        t = Table(rows, colWidths=[w * 0.42, w * 0.58])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.8),
            ("GRID", (0, 0), (-1, -1), 0.55, LINE),
            ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 2.4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ]))
        t.wrapOn(c, w, y)
        t.drawOn(c, x, y - t._height)

    def page_results(self, c, w, h):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 62, "R\u00c9SULTATS ET D\u00c9CISIONS")
        c.setStrokeColor(LINE)
        c.line(w / 2 - 60, h - 66, w / 2 + 60, h - 66)
        y = h - 90
        student = self.d["student"]
        c.setFont("Helvetica", 7)
        c.drawString(M, y, f"{student.last_name} {student.first_name} ({student.matricule})")
        y -= 16
        totals = self.d.get("totals_pdf")
        if totals is None:
            tot = self.d["table"]["total_coef"]
            totals = {
                "total_coef": self.d["table"]["total_coef"],
                "total_points": self.d["table"]["total_points"],
                "moy": self.d["annual_moy"],
                "classe": self.d["table"]["classe_annual"],
                "rank": self.d["annual_rank"],
                "out_of": self.d["annual_out_of"],
                "mention": self.d["annual_mention"],
                "decision": self.d["annual_decision"],
            }
        self._totals_block(c, M, y, w - 2 * M, totals)
        y -= 150
        # pa peryod
        rows = [[p["cycle_label"], (f"{p['moy']:.2f}" if p["moy"] is not None else "\u2014"),
                 (f"{p['class_moy']:.2f}" if p["class_moy"] is not None else "\u2014"),
                 (f"{p['rank']}" if p["rank"] else "\u2014"), p["decision"]] for p in self.d["per_period"]]
        t = Table([["P\u00e9riode", "Moyenne /20", "Moy. classe", "Place", "D\u00e9cision"]] + rows,
                  colWidths=[(w - 2 * M) * x for x in (0.30, 0.15, 0.15, 0.12, 0.28)])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.6),
            ("GRID", (0, 0), (-1, -1), 0.55, LINE),
            ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        t.wrapOn(c, w - 2 * M, y)
        t.drawOn(c, M, y - t._height)
        y -= t._height + 30
        self._sig_line(c, M + 6, y - 40, "Le Directeur : ")
        self._sig_line(c, M + 170, y - 40, "Le Parent")
        self._footer(c, w)

    def page_observations(self, c, w, h):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 62, "OBSERVATIONS \u2014 CONDUITE \u2014 CORRESPONDANCE")
        c.setStrokeColor(LINE)
        c.line(w / 2 - 60, h - 66, w / 2 + 60, h - 66)
        c.setStrokeColor(LINE)
        y = h - 95
        while y > 70:
            c.setLineWidth(0.35)
            c.line(M + 6, y, w - M - 6, y)
            y -= 21
        self._sig_line(c, M, 58, "Visa des parents")
        self._sig_line(c, M + 170, 58, "Le Titulaire")
        self._footer(c, w)

    def page_officiel(self, c, w, h):
        self._frame(c, w, h)
        self._std_header(c, w, h)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w / 2, h - 62, "EXAMEN OFFICIELS")
        c.setStrokeColor(LINE)
        c.line(w / 2 - 60, h - 66, w / 2 + 60, h - 66)
        inner = w - 2 * M
        header = ["MATI\u00c8RES", "PROFESSEUR", "NOTE /20"]
        rows = []
        for o in self.d["officials"]:
            sc = o["score"]
            rows.append([o["subject_name"][:28], str(o["teacher"])[:18],
                         f"{float(sc):.2f}" if sc is not None else "\u2014"])
        t = Table([header] + rows, colWidths=[inner * 0.36, inner * 0.42, inner * 0.22], repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("GRID", (0, 0), (-1, -1), 0.55, LINE),
            ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]))
        t.wrapOn(c, inner, h)
        top = h - 88
        t.drawOn(c, M, top - t._height)
        if self.carnet.show_graph and self.d["chart_data"]:
            drawing = self._pie(inner)
            renderPDF.draw(drawing, c, M, max(top - t._height - drawing.height - 16, 46))
        y = 44
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(M, y, "D\u00e9cision de fin d'ann\u00e9e : " + str(self.d["annual_decision"]))
        self._footer(c, w)

    def _pie(self, width):
        labels = self.d["chart_labels"]
        data = self.d["chart_data"]
        dr = Drawing(min(width, 250), 150)
        pie = Pie()
        pie.x, pie.y, pie.width, pie.height = 55, 10, 130, 130
        pie.data = data
        pie.labels = None
        pie.slices.strokeColor = colors.white
        from reportlab.lib.colors import HexColor as HC
        palette = ["#0d6efd", "#6610f2", "#d63384", "#198754", "#fd7e14", "#dc3545", "#20c997", "#6f42c1", "#ffc107", "#0dcaf0"]
        for i, col in enumerate(palette):
            if i < len(data):
                pie.slices[i].fillColor = HC(col)
        dr.add(pie)
        # legend manouel
        y = 138
        for i, lab in enumerate(labels[:10]):
            col = palette[i % len(palette)]
            dr.add(__import__("reportlab.graphics.shapes", fromlist=["Rect"]).Rect(195, y - 2, 7, 7, fillColor=HC(col), strokeColor=None))
            s = ParagraphStyle("l", fontName="Helvetica", fontSize=5.2)
            p = Paragraph(f"{lab} ({data[i]:.0f})", s)
            p.wrapOn(dr, 60, 10)
            dr.add(p)
            p.translate(205, y)
            y -= 12
        return dr

    def page_back(self, c, w, h):
        self._frame(c, w, h)
        car = self.carnet
        y = h / 2 + 60
        if self.logo_path:
            try:
                img = ImageReader(self.logo_path)
                bw = 56
                iw, ih = img.getSize()
                c.drawImage(img, (w - bw) / 2, y, bw, min(ih * bw / iw, 56))
                y -= 74
            except Exception:
                y -= 10
        c.setFont("Helvetica-Bold", 10.5)
        c.drawCentredString(w / 2, y, car.school_name)
        y -= 14
        c.setFont("Helvetica-Oblique", 7.5)
        c.drawCentredString(w / 2, y, car.slogan.upper())
        y -= 26
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(w / 2, y, f"Ann\u00e9e Acad\u00e9mique {self.d['classroom'].school_year.label if self.d['classroom'] else ''}")
        y -= 22
        c.setFont("Helvetica-Oblique", 7.5)
        c.drawCentredString(w / 2, y, "Gardez ce carnet avec soin pendant toute l'ann\u00e9e.")
        self._footer(c, w)

    def page_blank(self, c, w, h):
        self._frame(c, w, h)

    # ---------- asanblaj ----------
    def build_pages(self):
        data = self.d
        pages = [
            {"kind": "cover"},
            {"kind": "reglement"},
            {"kind": "identification"},
        ]
        rows = data["table"]["rows"]
        if rows:
            row_h = 13.5
            max_per_page = 14
            chunks = [rows[i:i + max_per_page] for i in range(0, len(rows), max_per_page)]
            for idx, chunk in enumerate(chunks, start=1):
                pages.append({"kind": "notes", "chunk": chunk,
                              "part": idx, "nparts": len(chunks),
                              "with_totals": idx == len(chunks)})
        pages.append({"kind": "results"})
        if data["is_official"]:
            pages.append({"kind": "officiel"})
        pages.append({"kind": "observations"})
        pages.append({"kind": "back"})
        return pages

    def _draw_one(self, c, page, w, h):
        kind = page["kind"]
        self.paid = bool(self.d.get("paid", False)) if isinstance(self.d, dict) else False
        if kind == "cover":
            self.page_cover(c, w, h)
        elif kind == "reglement":
            self.page_reglement(c, w, h)
        elif kind == "identification":
            self.page_identification(c, w, h)
        elif kind == "notes":
            totals = None
            if page.get("with_totals"):
                self.d["totals_pdf"] = {
                    "total_coef": self.d["table"]["total_coef"],
                    "total_points": self.d["table"]["total_points"],
                    "moy": self.d["annual_moy"],
                    "classe": self.d["table"]["classe_annual"],
                    "rank": self.d["annual_rank"],
                    "out_of": self.d["annual_out_of"],
                    "mention": self.d["annual_mention"],
                    "decision": self.d["annual_decision"],
                }
                totals = self.d["totals_pdf"]
            self.page_notes(c, w, h, page["chunk"], page["part"], page["nparts"],
                            self.d["per_period"], totals)
        elif kind == "results":
            self.page_results(c, w, h)
        elif kind == "officiel":
            self.page_officiel(c, w, h)
        elif kind == "observations":
            self.page_observations(c, w, h)
        elif kind == "back":
            self.page_back(c, w, h)
        else:
            self.page_blank(c, w, h)
        if kind != "blank":
            if not self.paid:
                self._stamp_unpaid(c, w, h)
                if kind == "notes":
                    self._cycle_badge(c, w, h, False)
            else:
                if kind in ("identification", "results"):
                    self._stamp_valid(c, w - 82, h - 52)
                if kind == "notes":
                    self._cycle_badge(c, w, h, True)

    def render(self, mod="lekti"):
        buf = io.BytesIO()
        pages = self.build_pages()
        if mod == "livret":
            c = rl_canvas.Canvas(buf, pagesize=(A4LW, A4LH))
            while len(pages) % 4:
                pages.append({"kind": "blank"})
            sides = livret_sides(list(range(len(pages))))
            total_sides = len(sides)
            for i, side in enumerate(sides):
                for half, page_no in enumerate(side):
                    if page_no is None:
                        continue
                    page = pages[page_no]
                    if page is None:
                        continue
                    if page is None:
                        continue
                    x0 = 0 if half == 0 else (A4LW - A5W)
                    c.saveState()
                    c.translate(x0, 0)
                    c.setFillColor(colors.white)
                    c.rect(0, 0, A5W, A5H, stroke=0, fill=1)
                    c.setStrokeColor(self.border)
                    c.setLineWidth(0.4)
                    c.line(A5W, 0, A5W, A5H)
                    self._draw_one(c, page, A5W, A5H)
                    c.restoreState()
                c.showPage()
            c.save()
        else:
            c = rl_canvas.Canvas(buf, pagesize=A5)
            for page in pages:
                c.saveState()
                c.setFillColor(colors.white)
                c.rect(0, 0, A5W, A5H, stroke=0, fill=1)
                self._draw_one(c, page, A5W, A5H)
                c.restoreState()
                c.showPage()
            c.save()
        return buf.getvalue()
