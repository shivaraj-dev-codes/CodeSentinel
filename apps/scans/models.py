"""Scan and finding models."""
import uuid

from django.conf import settings
from django.db import models


class ScanStatus(models.TextChoices):
    """Lifecycle stages of a scan task."""

    PENDING = "pending", "Pending"
    CLONING = "cloning", "Cloning Repository"
    ANALYZING = "analyzing", "Analyzing Files"
    RUNNING_ML = "running_ml", "Running ML Detection"
    AGGREGATING = "aggregating", "Aggregating Results"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Scan(models.Model):
    """
    Represents one full analysis run on a repository at a specific commit.
    All progress and result counters are updated in-place by the Celery task.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        "repositories.Repository",
        on_delete=models.CASCADE,
        related_name="scans",
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="triggered_scans",
    )

    commit_sha = models.CharField(max_length=40)
    branch = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
    )
    progress_percent = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Summary counters — updated at the end of the scan
    total_findings = models.IntegerField(default=0)
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    low_count = models.IntegerField(default=0)
    info_count = models.IntegerField(default=0)

    # Code stats
    lines_of_code = models.IntegerField(default=0)
    files_scanned = models.IntegerField(default=0)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "scans"
        verbose_name = "Scan"
        verbose_name_plural = "Scans"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.repository.full_name} @ {self.commit_sha[:7]} ({self.status})"

    @property
    def is_running(self) -> bool:
        """True if the scan is still in an active processing state."""
        return self.status in (
            ScanStatus.PENDING,
            ScanStatus.CLONING,
            ScanStatus.ANALYZING,
            ScanStatus.RUNNING_ML,
            ScanStatus.AGGREGATING,
        )
