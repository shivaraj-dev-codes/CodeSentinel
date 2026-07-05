"""Serializers for Finding and Rule models."""
from rest_framework import serializers

from .models import Finding, FindingStatus, Rule


class RuleSerializer(serializers.ModelSerializer):
    """Lightweight rule representation embedded in Finding responses."""

    class Meta:
        model = Rule
        fields = ["id", "rule_id_slug", "name", "category", "severity", "owasp_category", "cwe_id", "language"]


class FindingSerializer(serializers.ModelSerializer):
    """Full finding detail including the rule and triage state."""

    rule = RuleSerializer(read_only=True)
    suppressed_by_email = serializers.CharField(source="suppressed_by.email", read_only=True, default=None)
    repository_name = serializers.CharField(source="scan.repository.full_name", read_only=True)
    scan_branch = serializers.CharField(source="scan.branch", read_only=True)

    class Meta:
        model = Finding
        fields = [
            "id",
            "scan",
            "rule",
            "repository_name",
            "scan_branch",
            "file_path",
            "line_start",
            "line_end",
            "column_start",
            "column_end",
            "severity",
            "title",
            "description",
            "fix_suggestion",
            "code_snippet",
            "confidence_score",
            "source",
            "owasp_category",
            "cwe_id",
            "status",
            "suppressed_reason",
            "suppressed_by_email",
            "suppressed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "scan", "rule", "created_at", "updated_at",
            "repository_name", "scan_branch", "suppressed_by_email",
        ]


class FindingListSerializer(serializers.ModelSerializer):
    """Compact finding representation for list views — omits large text fields."""

    rule_name = serializers.CharField(source="rule.name", read_only=True)
    rule_category = serializers.CharField(source="rule.category", read_only=True)
    cwe_id = serializers.CharField(source="rule.cwe_id", read_only=True)

    class Meta:
        model = Finding
        fields = [
            "id",
            "scan",
            "file_path",
            "line_start",
            "line_end",
            "severity",
            "title",
            "rule_name",
            "rule_category",
            "cwe_id",
            "confidence_score",
            "source",
            "status",
            "created_at",
        ]


class UpdateFindingStatusSerializer(serializers.ModelSerializer):
    """PATCH payload for triaging a finding."""

    class Meta:
        model = Finding
        fields = ["status", "suppressed_reason"]

    def validate_status(self, value):
        """Ensure the status transition is valid."""
        allowed = [s for s, _ in FindingStatus.choices]
        if value not in allowed:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(allowed)}.")
        return value
