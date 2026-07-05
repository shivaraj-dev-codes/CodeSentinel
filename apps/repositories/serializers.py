"""Serializers for the repositories app."""
from rest_framework import serializers

from .models import Repository


class RepositorySerializer(serializers.ModelSerializer):
    """Full repository detail, including computed health score."""

    health_score = serializers.IntegerField(read_only=True)
    scan_count = serializers.SerializerMethodField()
    open_findings_count = serializers.SerializerMethodField()

    class Meta:
        model = Repository
        fields = [
            "id",
            "name",
            "full_name",
            "github_repo_url",
            "clone_url",
            "default_branch",
            "description",
            "is_private",
            "language",
            "health_score",
            "scan_count",
            "open_findings_count",
            "last_scanned_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_scan_count(self, obj) -> int:
        """Total number of scans triggered for this repository."""
        return obj.scans.count()

    def get_open_findings_count(self, obj) -> int:
        """Open findings across all scans for this repository."""
        from apps.findings.models import Finding, FindingStatus

        return Finding.objects.filter(
            scan__repository=obj, status=FindingStatus.OPEN
        ).count()


class AddRepositorySerializer(serializers.Serializer):
    """Payload to add a GitHub repository by its full name (owner/repo)."""

    full_name = serializers.CharField(
        help_text="GitHub full repository name, e.g. 'octocat/Hello-World'"
    )


class GitHubRepoSerializer(serializers.Serializer):
    """Shape of a GitHub API repository object returned to the frontend."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    html_url = serializers.URLField()
    clone_url = serializers.URLField()
    default_branch = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    private = serializers.BooleanField()
    language = serializers.CharField(allow_null=True)
    already_connected = serializers.BooleanField()
