import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TAG_RE = re.compile(r"<[^>]+>")


def _style(tag):
    styles = getSampleStyleSheet()
    mapping = {
        "h1": "Heading1", "h2": "Heading2", "h3": "Heading3", "h4": "Heading4",
    }
    base = styles[mapping.get(tag, "Normal")]
    return ParagraphStyle(name=f"{tag}-{id(base)}", parent=base, fontName="Helvetica")


def html_to_pdf(title, body_html, header_text="", footer_text="", watermark=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=25 * mm, bottomMargin=20 * mm,
        title=title or "Document",
    )

    story = []
    pos = 0
    block_re = re.compile(r"<(h1|h2|h3|h4|p|ul|ol|table)([^>]*)>(.*?)</\1>", re.S)
    void_re = re.compile(r"<(hr)([^>]*)/?>", re.S)

    def add_blocks():
        nonlocal pos
        matches = sorted(
            list(block_re.finditer(body_html)) + list(void_re.finditer(body_html)),
            key=lambda m: m.start(),
        )
        for match in matches:
            gap = body_html[pos:match.start()].strip()
            if gap:
                story.append(Paragraph(TAG_RE.sub("", gap), _style("p")))
            tag = match.group(1)
            inner = match.group(0)
            if tag in ("ul", "ol"):
                for item in re.findall(r"<li[^>]*>(.*?)</li>", inner, re.S):
                    story.append(Paragraph(f"• {TAG_RE.sub('', item)}", _style("li")))
            elif tag == "table":
                rows = re.findall(r"<tr[^>]*>(.*?)</tr>", inner, re.S)
                data = [
                    [Paragraph(TAG_RE.sub('', c), _style("td"))
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                    for row in rows
                ]
                if data:
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]))
                    story.append(table)
            elif tag == "hr":
                story.append(Spacer(1, 6))
            else:
                text = TAG_RE.sub("", inner).strip()
                if text:
                    story.append(Paragraph(text, _style(tag)))
                story.append(Spacer(1, 4))
            pos = match.end()
        tail = body_html[pos:].strip()
        if tail:
            story.append(Paragraph(TAG_RE.sub("", tail), _style("p")))

    add_blocks()

    def draw_frame(canvas, doc_obj):
        canvas.saveState()
        if header_text:
            canvas.setFont("Helvetica", 9)
            canvas.drawCentredString(A4[0] / 2, A4[1] - 12 * mm, header_text)
        if footer_text:
            canvas.setFont("Helvetica", 9)
            canvas.drawCentredString(A4[0] / 2, 10 * mm, footer_text)
        if watermark:
            canvas.setFont("Helvetica", 60)
            canvas.setFillColorRGB(0.92, 0.92, 0.92)
            canvas.saveState()
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, watermark)
            canvas.restoreState()
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_frame, onLaterPages=draw_frame)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
