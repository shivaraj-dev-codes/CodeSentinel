"""Serializers for Scan objects."""
from rest_framework import serializers

from .models import Scan, ScanStatus


class ScanSerializer(serializers.ModelSerializer):
    """Full scan detail serializer — used for list and detail views."""

    repository_name = serializers.CharField(source="repository.full_name", read_only=True)
    triggered_by_email = serializers.CharField(source="triggered_by.email", read_only=True, default=None)
    is_running = serializers.BooleanField(read_only=True)
    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            "id",
            "repository",
            "repository_name",
            "triggered_by",
            "triggered_by_email",
            "commit_sha",
            "branch",
            "status",
            "progress_percent",
            "is_running",
            "started_at",
            "completed_at",
            "error_message",
            "total_findings",
            "critical_count",
            "high_count",
            "medium_count",
            "low_count",
            "info_count",
            "lines_of_code",
            "files_scanned",
            "duration_seconds",
            "duration_display",
        ]
        read_only_fields = fields

    def get_duration_display(self, obj) -> str | None:
        """Human-readable scan duration, e.g. '1m 23s'."""
        if obj.duration_seconds is None:
            return None
        minutes, seconds = divmod(int(obj.duration_seconds), 60)
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


class TriggerScanSerializer(serializers.Serializer):
    """Payload to trigger a new scan on a repository."""

    branch = serializers.CharField(max_length=255, default="main")
    commit_sha = serializers.CharField(
        max_length=40,
        required=False,
        allow_blank=True,
        help_text="Optional commit SHA; defaults to the HEAD of the selected branch.",
    )
