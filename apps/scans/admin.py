"""Admin configuration for the scans app."""
from django.contrib import admin

from .models import Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    """Scan admin with status filters."""

    list_display = ("id", "repository", "branch", "status", "total_findings", "critical_count", "started_at")
    list_filter = ("status",)
    search_fields = ("repository__full_name", "commit_sha", "branch")
    readonly_fields = ("id", "started_at", "completed_at", "duration_seconds")
    raw_id_fields = ("repository", "triggered_by")
