"""Admin configuration for the findings app."""
from django.contrib import admin

from .models import Finding, Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("rule_id_slug", "name", "category", "severity", "language")
    list_filter = ("severity", "category", "language")
    search_fields = ("rule_id_slug", "name")
    readonly_fields = ("id",)


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "file_path", "line_start", "confidence_score", "source")
    list_filter = ("severity", "status", "source")
    search_fields = ("title", "file_path", "rule__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("scan", "rule", "suppressed_by")
