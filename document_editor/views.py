import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.views import teaching_staff_required as staff_required
from core.models import SiteSettings

from .docx_export import html_to_docx
from .models import Document, DocumentTemplate
from .pdf_export import html_to_pdf


@login_required
@staff_required
def index(request):
    documents = Document.objects.all()
    templates = DocumentTemplate.objects.all()
    return render(request, "document_editor/index.html", {
        "documents": documents,
        "templates": templates,
    })


@login_required
@staff_required
def editor(request, pk=None):
    document = None
    if pk:
        document = get_object_or_404(Document, pk=pk)
    template_id = request.GET.get("modele")
    template = DocumentTemplate.objects.filter(pk=template_id).first() if template_id else None

    if request.method == "POST":
        title = request.POST.get("title", "Sans titre")
        category = request.POST.get("category", "LETTRE")
        body_html = request.POST.get("body_html", "")
        watermark = request.POST.get("watermark", "")
        if document is None:
            document = Document(created_by=request.user)
        document.title = title
        document.category = category
        document.body_html = body_html
        document.watermark = watermark
        document.template = template
        document.save()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(json.dumps({"id": document.pk, "status": "saved"}),
                                content_type="application/json")
        messages.success(request, "Document enregistré.")
        if request.POST.get("action") == "stay":
            return redirect("document_editor:editor", pk=document.pk)
        return redirect("document_editor:index")

    initial_watermark = ""
    if document and document.watermark:
        initial_watermark = document.watermark
    elif template:
        initial_watermark = template.watermark
    initial_body = template.body_html if (template and not document) else (
        document.body_html if document else ""
    )

    return render(request, "document_editor/editor.html", {
        "document": document,
        "template": template,
        "templates": DocumentTemplate.objects.all(),
        "template_categories": DocumentTemplate.CATEGORIES,
        "initial_watermark": initial_watermark,
        "initial_body": initial_body,
        "site": SiteSettings.load(),
    })


@login_required
@staff_required
def duplicate(request, pk):
    document = get_object_or_404(Document, pk=pk)
    copy = Document.objects.create(
        title=f"{document.title} (copie)", category=document.category,
        template=document.template, body_html=document.body_html,
        watermark=document.watermark, created_by=request.user,
    )
    return redirect("document_editor:editor", pk=copy.pk)


@login_required
@staff_required
@require_POST
def delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    document.delete()
    messages.success(request, "Document supprimé.")
    return redirect("document_editor:index")


def _render_context(document):
    site = SiteSettings.load()
    header_text = f"{site.name} — {site.short_name}"
    footer_text = site.copyright_text
    watermark = document.watermark
    if document.template:
        header_text = document.template.header_text or header_text
        footer_text = document.template.footer_text or footer_text
        watermark = watermark or document.template.watermark
    return {
        "document": document,
        "site": site,
        "header_text": header_text,
        "footer_text": footer_text,
        "watermark": watermark,
    }


@login_required
@staff_required
def export_docx(request, pk):
    document = get_object_or_404(Document, pk=pk)
    ctx = _render_context(document)
    doc = html_to_docx(document.title, document.body_html,
                       ctx["header_text"], ctx["footer_text"], ctx["watermark"])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    response["Content-Disposition"] = f'attachment; filename="{document.title}.docx"'
    doc.save(response)
    return response


@login_required
@staff_required
def export_pdf(request, pk):
    document = get_object_or_404(Document, pk=pk)
    ctx = _render_context(document)
    pdf = html_to_pdf(document.title, document.body_html,
                      ctx["header_text"], ctx["footer_text"], ctx["watermark"])
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{document.title}.pdf"'
    return response


@login_required
@staff_required
def preview(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, "document_editor/preview.html", _render_context(document))
