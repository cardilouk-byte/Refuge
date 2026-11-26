import re
from pathlib import Path

from docx import Document as DocxDocument
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

ALIGNMENTS = {
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

TAG_RE = re.compile(r"<[^>]+>")


def _apply_runs(paragraph, html):
    bold = bool(re.search(r"<strong|<b[ >]", html))
    italic = bool(re.search(r"<em|<i[ >]", html))
    underline = bool(re.search(r"<u[ >]", html))
    color = re.search(r"color:\s*(#[0-9a-fA-F]{3,6})", html)
    size = re.search(r"font-size:\s*(\d+)px", html)
    for part in re.split(r"<[^>]+>", html):
        if not part.strip():
            continue
        run = paragraph.add_run(part)
        run.font.name = "Poppins"
        run.font.size = Pt(int(size.group(1)) * 0.75 if size else 11)
        run.bold = bold
        run.italic = italic
        run.underline = underline
        if color:
            run.font.color.rgb = RGBColor.from_string(color.group(1).lstrip("#").upper())


def _add_block(doc, tag, html):
    style_map = {"h1": "Heading 1", "h2": "Heading 2", "h3": "Heading 3", "h4": "Heading 4"}
    if tag in ("ul", "ol"):
        items = re.findall(r"<li[^>]*>(.*?)</li>", html, re.S)
        for item in items:
            p = doc.add_paragraph(style="List Bullet" if tag == "ul" else "List Number")
            _apply_runs(p, item)
        return
    if tag == "table":
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
        if not rows:
            return
        parsed = [[c.strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
                  for row in rows]
        cols = max(len(r) for r in parsed)
        table = doc.add_table(rows=len(parsed), cols=cols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r, row in enumerate(parsed):
            for c, cell in enumerate(row):
                if c < cols:
                    table.rows[r].cells[c].text = TAG_RE.sub("", cell)
        return
    if tag == "img":
        match = re.search(r'src="([^"]+)"', html)
        if match:
            src = match.group(1)
            from django.conf import settings as dj_settings
            if src.startswith("/media/"):
                local = Path(dj_settings.MEDIA_ROOT) / src[len("/media/"):]
                if local.exists():
                    doc.add_picture(str(local), width=Pt(120))
        return
    if tag == "hr":
        return

    paragraph = doc.add_paragraph(style=style_map.get(tag, "Normal"))
    if tag == "p":
        if "text-align: center" in html:
            paragraph.alignment = ALIGNMENTS["center"]
        elif "text-align: right" in html:
            paragraph.alignment = ALIGNMENTS["right"]
        elif "text-align: justify" in html:
            paragraph.alignment = ALIGNMENTS["justify"]
    _apply_runs(paragraph, html)


BLOCK_RE = re.compile(r"<(h1|h2|h3|h4|p|ul|ol|table)([^>]*)>(.*?)</\1>", re.S)
VOID_RE = re.compile(r"<(img|hr)([^>]*)/?>", re.S)


def html_to_docx(title, body_html, header_text="", footer_text="", watermark=""):
    doc = DocxDocument()
    if title:
        doc.core_properties.title = title

    section = doc.sections[0]
    if header_text:
        section.header.paragraphs[0].text = header_text
        section.header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if footer_text:
        section.footer.paragraphs[0].text = footer_text
        section.footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if watermark:
        run = section.header.paragraphs[0].add_run(f" {watermark} ")
        run.font.size = Pt(48)
        run.font.color.rgb = RGBColor(210, 210, 210)

    matches = sorted(
        list(BLOCK_RE.finditer(body_html)) + list(VOID_RE.finditer(body_html)),
        key=lambda m: m.start(),
    )
    pos = 0
    for match in matches:
        gap = body_html[pos:match.start()].strip()
        if gap:
            _add_block(doc, "p", gap)
        _add_block(doc, match.group(1), match.group(0))
        pos = match.end()
    tail = body_html[pos:].strip()
    if tail:
        _add_block(doc, "p", tail)
    return doc
