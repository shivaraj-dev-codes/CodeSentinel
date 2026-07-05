"""Admin configuration for the repositories app."""
from django.contrib import admin

from .models import Repository


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """Repository admin."""

    list_display = ("full_name", "owner", "language", "is_private", "last_scanned_at", "created_at")
    list_filter = ("is_private", "language")
    search_fields = ("name", "full_name", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at", "health_score")
    raw_id_fields = ("owner",)
