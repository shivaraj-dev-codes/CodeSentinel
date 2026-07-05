"""Scan trigger and status endpoints."""
import requests
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.repositories.models import Repository

from .models import Scan, ScanStatus
from .serializers import ScanSerializer, TriggerScanSerializer


class TriggerScanView(APIView):
    """POST /api/repositories/{id}/scans/ — trigger a new scan."""

    @extend_schema(summary="Trigger a new scan", request=TriggerScanSerializer, responses={202: ScanSerializer})
    def post(self, request, repo_pk):
        repo = get_object_or_404(Repository, pk=repo_pk, owner=request.user)

        # Check for a running scan on this repository
        running = repo.scans.filter(status__in=[
            ScanStatus.PENDING,
            ScanStatus.CLONING,
            ScanStatus.ANALYZING,
            ScanStatus.RUNNING_ML,
            ScanStatus.AGGREGATING,
        ]).first()

        if running:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "SCAN_ALREADY_RUNNING",
                        "message": "A scan is already in progress for this repository.",
                        "details": {"scan_id": str(running.id)},
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = TriggerScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.validated_data.get("branch") or repo.default_branch
        commit_sha = serializer.validated_data.get("commit_sha") or "HEAD"

        # Resolve HEAD to an actual SHA via GitHub API if the user didn't provide one
        if commit_sha == "HEAD" and request.user.has_github_connected:
            try:
                gh_resp = requests.get(
                    f"https://api.github.com/repos/{repo.full_name}/commits/{branch}",
                    headers={
                        "Authorization": f"token {request.user.github_token}",
                        "Accept": "application/vnd.github+json",
                    },
                    timeout=10,
                )
                if gh_resp.ok:
                    commit_sha = gh_resp.json().get("sha", "HEAD")[:40]
            except Exception:
                pass  # Fall back to "HEAD" as a placeholder

        scan = Scan.objects.create(
            repository=repo,
            triggered_by=request.user,
            branch=branch,
            commit_sha=commit_sha,
            status=ScanStatus.PENDING,
        )

        # Enqueue the Celery task
        from .tasks import run_scan

        run_scan.delay(str(scan.id))

        return Response(
            {"success": True, "data": ScanSerializer(scan).data},
            status=status.HTTP_202_ACCEPTED,
        )


class ScanListView(generics.ListAPIView):
    """GET /api/scans/ — list all scans for repositories owned by the current user."""

    serializer_class = ScanSerializer

    def get_queryset(self):
        return (
            Scan.objects.filter(repository__owner=self.request.user)
            .select_related("repository", "triggered_by")
            .order_by("-started_at")
        )

    @extend_schema(summary="List all scans")
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})


class ScanDetailView(generics.RetrieveAPIView):
    """GET /api/scans/{id}/ — full scan detail including counters and status."""

    serializer_class = ScanSerializer

    def get_queryset(self):
        return Scan.objects.filter(repository__owner=self.request.user).select_related(
            "repository", "triggered_by"
        )

    @extend_schema(summary="Get scan detail")
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"success": True, "data": self.get_serializer(instance).data})


class CancelScanView(APIView):
    """POST /api/scans/{id}/cancel/ — attempt to cancel a running scan."""

    @extend_schema(summary="Cancel a scan")
    def post(self, request, pk):
        scan = get_object_or_404(Scan, pk=pk, repository__owner=request.user)

        if not scan.is_running:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "SCAN_NOT_RUNNING",
                        "message": "Only in-progress scans can be cancelled.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        scan.status = ScanStatus.FAILED
        scan.error_message = "Cancelled by user."
        scan.completed_at = timezone.now()
        scan.save(update_fields=["status", "error_message", "completed_at"])

        return Response({"success": True, "data": {"message": "Scan cancelled."}})
