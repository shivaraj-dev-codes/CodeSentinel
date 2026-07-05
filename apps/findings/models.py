"""Finding and Rule models."""
import uuid

from django.conf import settings
from django.db import models


class FindingStatus(models.TextChoices):
    """Lifecycle states a finding can be in after detection."""

    OPEN = "open", "Open"
    RESOLVED = "resolved", "Resolved"
    SUPPRESSED = "suppressed", "Suppressed"
    FALSE_POSITIVE = "false_positive", "False Positive"


class Severity(models.TextChoices):
    """Severity levels — must match the design system colors exactly."""

    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"
    INFO = "info", "Info"


class Rule(models.Model):
    """
    A vulnerability detection rule (from Semgrep or the ML model).
    Rules are shared across scans — findings reference them by FK.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_id_slug = models.CharField(max_length=200, unique=True)  # e.g. "python.sql-injection-via-format"
    name = models.CharField(max_length=500)
    description = models.TextField()
    category = models.CharField(max_length=100)  # e.g. "SQL Injection", "Command Injection"
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    owasp_category = models.CharField(max_length=100, blank=True)  # e.g. "A03:2021 – Injection"
    cwe_id = models.CharField(max_length=20, blank=True)  # e.g. "CWE-89"
    language = models.CharField(max_length=50, default="python")

    class Meta:
        db_table = "rules"
        verbose_name = "Rule"
        verbose_name_plural = "Rules"

    def __str__(self) -> str:
        return f"{self.rule_id_slug} ({self.severity})"


class Finding(models.Model):
    """
    A single vulnerability finding detected during a scan.
    Stores both the raw code snippet and AI-generated fix suggestion.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan = models.ForeignKey(
        "scans.Scan",
        on_delete=models.CASCADE,
        related_name="findings",
    )
    rule = models.ForeignKey(
        Rule,
        on_delete=models.PROTECT,  # PROTECT: don't lose findings if a rule is retired
        related_name="findings",
    )

    # Location in the source file
    file_path = models.CharField(max_length=1000)
    line_start = models.IntegerField()
    line_end = models.IntegerField()
    column_start = models.IntegerField(null=True, blank=True)
    column_end = models.IntegerField(null=True, blank=True)

    # Classification
    severity = models.CharField(max_length=20, choices=Severity.choices, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    fix_suggestion = models.TextField()
    code_snippet = models.TextField()
    confidence_score = models.FloatField()  # 0.0–1.0, higher = more confident
    source = models.CharField(max_length=20)  # 'semgrep' | 'ml_model' | 'combined'
    owasp_category = models.CharField(max_length=100, blank=True)
    cwe_id = models.CharField(max_length=20, blank=True)

    # Triage state
    status = models.CharField(
        max_length=20,
        choices=FindingStatus.choices,
        default=FindingStatus.OPEN,
        db_index=True,
    )
    suppressed_reason = models.TextField(blank=True)
    suppressed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suppressed_findings",
    )
    suppressed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "findings"
        verbose_name = "Finding"
        verbose_name_plural = "Findings"
        ordering = ["-severity", "-confidence_score"]
        indexes = [
            models.Index(fields=["scan", "severity"]),
            models.Index(fields=["scan", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.severity.upper()}: {self.title} ({self.file_path}:{self.line_start})"
