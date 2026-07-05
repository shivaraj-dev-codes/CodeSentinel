"""Repository model — represents a GitHub repo connected by a user."""
import uuid

from django.conf import settings
from django.db import models


class Repository(models.Model):
    """
    A GitHub repository that the user has connected to CodeSentinel.
    Stores enough metadata to trigger scans without re-fetching from GitHub each time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="repositories",
    )

    # GitHub-provided identifiers
    github_repo_id = models.BigIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)  # e.g. "my-awesome-app"
    full_name = models.CharField(max_length=512)  # e.g. "octocat/my-awesome-app"
    github_repo_url = models.URLField()  # HTML URL, e.g. https://github.com/...
    clone_url = models.URLField(blank=True)  # git clone URL
    default_branch = models.CharField(max_length=255, default="main")
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    language = models.CharField(max_length=100, blank=True)  # Primary language reported by GitHub

    # Scan metadata
    last_scanned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "repositories"
        verbose_name = "Repository"
        verbose_name_plural = "Repositories"
        ordering = ["-updated_at"]
        # One user cannot add the same GitHub repo twice
        unique_together = [("owner", "github_repo_id")]

    def __str__(self) -> str:
        return self.full_name

    @property
    def health_score(self) -> int:
        """
        Compute a 0–100 health score from the latest completed scan.
        Lower score = more critical/high findings relative to lines of code.
        """
        from apps.scans.models import Scan, ScanStatus

        latest = (
            self.scans.filter(status=ScanStatus.COMPLETED)
            .order_by("-started_at")
            .first()
        )
        if not latest:
            return 100  # No scans yet → assume healthy

        score = 100
        score -= latest.critical_count * 20
        score -= latest.high_count * 10
        score -= latest.medium_count * 3
        score -= latest.low_count * 1
        return max(0, min(100, score))
