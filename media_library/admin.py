from django.contrib import admin

from .models import MediaFile


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "category", "size_display", "uploaded_by", "created_at")
    list_filter = ("category",)
    search_fields = ("original_name",)
