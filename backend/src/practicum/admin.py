from django.contrib import admin
from .models import Answer


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "case",
        "attempt",
        "status",
        "created_at",
        "checked_by",
    )

    list_filter = (
        "status",
        "case",
        "created_at",
    )

    search_fields = (
        "user__username",
        "case__name",
    )

    readonly_fields = (
        "user",
        "case",
        "attempt",
        "text",
        "created_at",
    )

    fields = (
        "user",
        "case",
        "attempt",
        "text",
        "status",
        "comment",
        "checked_by",
        "checked_at",
    )