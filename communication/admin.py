from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "recipient", "created_at", "is_read_display")
    search_fields = ("subject", "body", "sender__username", "recipient__username")
    readonly_fields = ("created_at", "read_at")

    @admin.display(boolean=True, description="Lu")
    def is_read_display(self, obj):
        return obj.is_read
