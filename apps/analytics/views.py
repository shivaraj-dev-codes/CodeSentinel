"""Analytics and dashboard aggregation endpoints."""
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.findings.models import Finding, FindingStatus, Severity
from apps.repositories.models import Repository
from apps.scans.models import Scan, ScanStatus


class DashboardOverviewView(APIView):
    """GET /api/analytics/overview/ — top-level KPIs for the dashboard."""

    @extend_schema(summary="Dashboard overview stats")
    def get(self, request):
        user = request.user
        repos = Repository.objects.filter(owner=user)
        scans = Scan.objects.filter(repository__owner=user)
        findings = Finding.objects.filter(scan__repository__owner=user)

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        prev_week_ago = now - timedelta(days=14)

        open_findings = findings.filter(status=FindingStatus.OPEN)
        critical_open = open_findings.filter(severity=Severity.CRITICAL)

        scans_this_week = scans.filter(started_at__gte=week_ago, status=ScanStatus.COMPLETED).count()
        scans_last_week = scans.filter(
            started_at__gte=prev_week_ago, started_at__lt=week_ago, status=ScanStatus.COMPLETED
        ).count()

        open_count = open_findings.count()
        open_last_week = findings.filter(
            status=FindingStatus.OPEN, created_at__gte=prev_week_ago, created_at__lt=week_ago
        ).count()
        open_delta = open_count - open_last_week

        return Response(
            {
                "success": True,
                "data": {
                    "total_open_findings": open_count,
                    "open_findings_delta": open_delta,
                    "critical_issues": critical_open.count(),
                    "repos_connected": repos.count(),
                    "scans_this_week": scans_this_week,
                    "scans_last_week": scans_last_week,
                    "avg_scan_duration_seconds": scans.filter(
                        status=ScanStatus.COMPLETED, duration_seconds__isnull=False
                    ).aggregate(avg=Avg("duration_seconds"))["avg"],
                    "fix_rate_percent": _compute_fix_rate(findings),
                },
            }
        )


class SeverityTrendView(APIView):
    """GET /api/analytics/severity-trend/ — daily finding counts by severity over N days."""

    @extend_schema(summary="Severity trend over time")
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        user = request.user
        now = timezone.now()
        since = now - timedelta(days=days)

        findings = Finding.objects.filter(
            scan__repository__owner=user, created_at__gte=since
        )

        # Build a day-by-day series for each severity
        trend: dict[str, dict] = {}
        for finding in findings.values("created_at", "severity"):
            day = finding["created_at"].strftime("%Y-%m-%d")
            if day not in trend:
                trend[day] = {"date": day, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
            sev = finding["severity"]
            if sev in trend[day]:
                trend[day][sev] += 1

        # Fill in missing days with zeros
        result = []
        for i in range(days):
            day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
            result.append(trend.get(day, {"date": day, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}))

        return Response({"success": True, "data": result})


class TopVulnerabilityCategoriesView(APIView):
    """GET /api/analytics/top-vulnerability-categories/ — top N vulnerability categories."""

    @extend_schema(summary="Top vulnerability categories")
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        user = request.user

        categories = (
            Finding.objects.filter(scan__repository__owner=user, status=FindingStatus.OPEN)
            .values("rule__category")
            .annotate(count=Count("id"))
            .order_by("-count")[:limit]
        )

        data = [{"category": row["rule__category"] or "Uncategorised", "count": row["count"]} for row in categories]
        return Response({"success": True, "data": data})


class RepositoryHealthView(APIView):
    """GET /api/analytics/repository-health/ — health score and finding breakdown per repo."""

    @extend_schema(summary="Repository health scores")
    def get(self, request):
        repos = Repository.objects.filter(owner=request.user).prefetch_related("scans")

        data = []
        for repo in repos:
            latest_scan = (
                repo.scans.filter(status=ScanStatus.COMPLETED).order_by("-started_at").first()
            )
            data.append(
                {
                    "repository_id": str(repo.id),
                    "repository_name": repo.full_name,
                    "health_score": repo.health_score,
                    "critical": latest_scan.critical_count if latest_scan else 0,
                    "high": latest_scan.high_count if latest_scan else 0,
                    "medium": latest_scan.medium_count if latest_scan else 0,
                    "low": latest_scan.low_count if latest_scan else 0,
                    "last_scanned_at": repo.last_scanned_at,
                }
            )

        data.sort(key=lambda x: x["health_score"])
        return Response({"success": True, "data": data})


class FixRateView(APIView):
    """GET /api/analytics/fix-rate/ — resolved vs open findings over time."""

    @extend_schema(summary="Finding fix rate over time")
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        user = request.user
        now = timezone.now()
        since = now - timedelta(days=days)

        findings = Finding.objects.filter(scan__repository__owner=user, created_at__gte=since)

        daily: dict[str, dict] = {}
        for f in findings.values("created_at", "status"):
            day = f["created_at"].strftime("%Y-%m-%d")
            if day not in daily:
                daily[day] = {"date": day, "open": 0, "resolved": 0, "suppressed": 0}
            st = f["status"]
            if st in daily[day]:
                daily[day][st] += 1

        result = []
        for i in range(days):
            day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
            result.append(daily.get(day, {"date": day, "open": 0, "resolved": 0, "suppressed": 0}))

        return Response({"success": True, "data": result})


# ── Helpers ───────────────────────────────────────────────────────────────────


def _compute_fix_rate(findings) -> float:
    """Percentage of non-open findings out of total findings."""
    total = findings.count()
    if total == 0:
        return 0.0
    closed = findings.filter(status__in=[FindingStatus.RESOLVED, FindingStatus.SUPPRESSED, FindingStatus.FALSE_POSITIVE]).count()
    return round((closed / total) * 100, 1)
