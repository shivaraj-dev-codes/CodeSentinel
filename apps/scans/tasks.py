"""Celery scan task — orchestrates the full scan pipeline."""
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


def push_progress(channel_layer, scan_id: str, percent: int, status: str, message: str):
    """
    Update scan progress in the DB and broadcast to the WebSocket group.
    Wrapped in a try/except so a Redis failure does not abort the scan.
    """
    from .models import Scan

    try:
        Scan.objects.filter(id=scan_id).update(
            progress_percent=percent,
            status=status,
        )
    except Exception as exc:
        logger.warning("Could not update scan status in DB: %s", exc)

    try:
        async_to_sync(channel_layer.group_send)(
            f"scan_{scan_id}",
            {
                "type": "scan.progress",
                "percent": percent,
                "status": status,
                "message": message,
            },
        )
    except Exception as exc:
        logger.warning("Could not push WebSocket progress: %s", exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_scan(self, scan_id: str):
    """
    Main scan orchestration task.

    Stages:
      5%  → Clone / fetch repository files
      15% → Index files and count lines
      30% → Semgrep static analysis
      50% → Tree-sitter AST feature extraction
      70% → ML vulnerability detection (CodeBERT + XGBoost)
      85% → Merge, deduplicate, and score findings
      95% → Persist findings to database
      100%→ Complete
    """
    from .models import Scan, ScanStatus

    try:
        scan = Scan.objects.select_related("repository", "repository__owner").get(id=scan_id)
    except Scan.DoesNotExist:
        logger.error("Scan %s not found — aborting task.", scan_id)
        return

    channel_layer = get_channel_layer()
    start_time = time.monotonic()

    try:
        # ── Stage 1: Clone / fetch repository ─────────────────────────────
        push_progress(channel_layer, scan_id, 5, ScanStatus.CLONING, "Fetching repository contents…")

        with tempfile.TemporaryDirectory(prefix="codesentinel_") as tmp_dir:
            repo_path = Path(tmp_dir)
            _fetch_repository(scan, repo_path)

            # ── Stage 2: Discover files ────────────────────────────────────
            push_progress(channel_layer, scan_id, 15, ScanStatus.ANALYZING, "Indexing Python files…")
            file_list = _discover_python_files(repo_path)
            loc = _count_lines(file_list)

            Scan.objects.filter(id=scan_id).update(
                files_scanned=len(file_list),
                lines_of_code=loc,
            )

            # ── Stage 3: Semgrep static analysis ──────────────────────────
            push_progress(channel_layer, scan_id, 30, ScanStatus.ANALYZING, "Running Semgrep static analysis…")
            semgrep_findings = _run_semgrep(repo_path)

            # ── Stage 4: AST feature extraction ───────────────────────────
            push_progress(channel_layer, scan_id, 50, ScanStatus.ANALYZING, "Extracting AST code features…")
            ast_features = _extract_ast_features(file_list)

            # ── Stage 5: ML inference ──────────────────────────────────────
            push_progress(channel_layer, scan_id, 70, ScanStatus.RUNNING_ML, "Running ML vulnerability detection…")
            ml_findings = _run_ml_pipeline(ast_features, file_list)

            # ── Stage 6: Merge and score ───────────────────────────────────
            push_progress(channel_layer, scan_id, 85, ScanStatus.AGGREGATING, "Aggregating and scoring findings…")
            all_findings = _merge_findings(semgrep_findings, ml_findings)

            # ── Stage 7: Persist ───────────────────────────────────────────
            push_progress(channel_layer, scan_id, 95, ScanStatus.AGGREGATING, "Saving results to database…")
            _save_findings(scan, all_findings)
            _update_scan_summary(scan)

        # ── Stage 8: Complete ──────────────────────────────────────────────
        duration = time.monotonic() - start_time
        Scan.objects.filter(id=scan_id).update(
            completed_at=timezone.now(),
            duration_seconds=duration,
        )
        push_progress(channel_layer, scan_id, 100, ScanStatus.COMPLETED, "Scan complete.")

        # Update repository's last_scanned_at timestamp
        from apps.repositories.models import Repository

        Repository.objects.filter(id=scan.repository_id).update(last_scanned_at=timezone.now())

        logger.info("Scan %s completed in %.1fs — %d findings.", scan_id, duration, scan.total_findings)

    except Exception as exc:
        logger.exception("Scan %s failed: %s", scan_id, exc)
        Scan.objects.filter(id=scan_id).update(
            status=ScanStatus.FAILED,
            error_message=str(exc),
            completed_at=timezone.now(),
        )
        push_progress(channel_layer, scan_id, 0, ScanStatus.FAILED, f"Scan failed: {exc}")
        raise self.retry(exc=exc)


# ── Private helpers ────────────────────────────────────────────────────────────


def _fetch_repository(scan, target_path: Path) -> None:
    """
    Clone or download the repository at the scanned commit.
    Uses the GitHub API tarball endpoint to avoid requiring git on the worker.
    """
    import requests

    user = scan.repository.owner
    repo = scan.repository
    branch = scan.branch

    url = f"https://api.github.com/repos/{repo.full_name}/tarball/{branch}"
    headers = {}
    if user.has_github_connected:
        headers["Authorization"] = f"token {user.github_token}"

    response = requests.get(url, headers=headers, stream=True, timeout=60)
    if response.status_code == 404:
        # Repository might be public — try without auth
        response = requests.get(url, stream=True, timeout=60)

    response.raise_for_status()

    import tarfile

    tarball_path = target_path / "repo.tar.gz"
    with open(tarball_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    with tarfile.open(tarball_path) as tar:
        tar.extractall(target_path)

    tarball_path.unlink()


def _discover_python_files(root: Path) -> list[Path]:
    """Return all .py files under the given directory."""
    return [p for p in root.rglob("*.py") if not any(
        part.startswith(".") or part in ("venv", ".venv", "node_modules", "__pycache__")
        for part in p.parts
    )]


def _count_lines(files: list[Path]) -> int:
    """Count total source lines across all files."""
    total = 0
    for f in files:
        try:
            total += sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return total


def _run_semgrep(repo_path: Path) -> list[dict]:
    """Run Semgrep with the bundled rules and return parsed findings."""
    try:
        from ml.semgrep_runner import SemgrepRunner

        runner = SemgrepRunner()
        return runner.run(repo_path)
    except Exception as exc:
        logger.warning("Semgrep failed (non-fatal): %s", exc)
        return []


def _extract_ast_features(files: list[Path]) -> list[dict]:
    """Extract AST features from each file using the feature extractor."""
    try:
        from ml.feature_extractor import FeatureExtractor

        extractor = FeatureExtractor()
        return extractor.extract_from_files(files)
    except Exception as exc:
        logger.warning("AST extraction failed (non-fatal): %s", exc)
        return []


def _run_ml_pipeline(ast_features: list[dict], files: list[Path]) -> list[dict]:
    """Run the CodeBERT + XGBoost ML pipeline and return detected findings."""
    try:
        from ml.pipeline import VulnerabilityDetectionPipeline

        pipeline = VulnerabilityDetectionPipeline()
        return pipeline.predict(ast_features)
    except Exception as exc:
        logger.warning("ML pipeline failed (non-fatal): %s", exc)
        return []


def _merge_findings(semgrep: list[dict], ml: list[dict]) -> list[dict]:
    """
    Merge Semgrep and ML findings.
    Deduplicate by (file_path, line_start, rule_id/title).
    Prefer Semgrep findings when there is an overlap — higher precision.
    """
    seen = set()
    merged = []

    for finding in semgrep:
        key = (finding.get("file_path"), finding.get("line_start"), finding.get("rule_id", ""))
        if key not in seen:
            finding["source"] = "semgrep"
            merged.append(finding)
            seen.add(key)

    for finding in ml:
        key = (finding.get("file_path"), finding.get("line_start"), finding.get("title", ""))
        if key not in seen:
            finding["source"] = "ml_model"
            merged.append(finding)
            seen.add(key)

    return merged


def _save_findings(scan, all_findings: list[dict]) -> None:
    """Persist merged findings to the database in bulk."""
    from apps.findings.models import Finding, Rule

    finding_objects = []
    for raw in all_findings:
        # Get or create the rule record
        rule, _ = Rule.objects.get_or_create(
            rule_id_slug=raw.get("rule_id", f"ml_{raw.get('title', 'unknown')}").replace(" ", "_").lower()[:100],
            defaults={
                "name": raw.get("title", "Unknown Vulnerability"),
                "description": raw.get("description", ""),
                "category": raw.get("category", "Other"),
                "severity": raw.get("severity", "medium"),
                "owasp_category": raw.get("owasp_category", ""),
                "cwe_id": raw.get("cwe_id", ""),
                "language": "python",
            },
        )

        finding_objects.append(
            Finding(
                scan=scan,
                rule=rule,
                file_path=raw.get("file_path", "unknown"),
                line_start=raw.get("line_start", 1),
                line_end=raw.get("line_end", raw.get("line_start", 1)),
                column_start=raw.get("column_start"),
                column_end=raw.get("column_end"),
                severity=raw.get("severity", "medium"),
                title=raw.get("title", rule.name),
                description=raw.get("description", rule.description),
                fix_suggestion=raw.get("fix_suggestion", raw.get("fix", "")),
                code_snippet=raw.get("code_snippet", ""),
                confidence_score=raw.get("confidence_score", 0.85),
                source=raw.get("source", "semgrep"),
                owasp_category=raw.get("owasp_category", ""),
                cwe_id=raw.get("cwe_id", ""),
            )
        )

    Finding.objects.bulk_create(finding_objects, batch_size=500)


def _update_scan_summary(scan) -> None:
    """Re-count findings by severity and update the scan summary row."""
    from apps.findings.models import Finding
    from apps.scans.models import Scan

    counts = {
        row["severity"]: row["count"]
        for row in Finding.objects.filter(scan=scan).values("severity").annotate(
            count=__import__("django.db.models", fromlist=["Count"]).Count("id")
        )
    }

    total = sum(counts.values())
    Scan.objects.filter(id=scan.id).update(
        total_findings=total,
        critical_count=counts.get("critical", 0),
        high_count=counts.get("high", 0),
        medium_count=counts.get("medium", 0),
        low_count=counts.get("low", 0),
        info_count=counts.get("info", 0),
    )
