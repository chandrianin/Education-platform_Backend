from django.contrib import admin
from .models import (
    Indicator,
    IndicatorValue,
    MonthlyEnvironmentIndex
)


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "modality_coefficient",
        "is_active",
    )

    list_filter = ("is_active",)


@admin.register(IndicatorValue)
class IndicatorValueAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "indicator",
        "score",
        "period",
    )

    list_filter = (
        "indicator",
        "period",
    )

    search_fields = (
        "user__username",
    )


@admin.register(MonthlyEnvironmentIndex)
class MonthlyEnvironmentIndexAdmin(admin.ModelAdmin):
    list_display = (
        "period",
        "index_value",
        "calculated_at",
    )

    ordering = ("-period",)
