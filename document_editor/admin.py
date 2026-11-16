from django.contrib import admin

from .models import Document, DocumentTemplate


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "header_text", "watermark")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_by", "updated_at")
    list_filter = ("category",)
    search_fields = ("title",)
