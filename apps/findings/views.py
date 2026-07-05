"""Finding list, detail, and triage endpoints."""
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Finding, FindingStatus
from .serializers import FindingListSerializer, FindingSerializer, UpdateFindingStatusSerializer


class FindingListView(generics.ListAPIView):
    """
    GET /api/findings/ — all findings across all repos, filterable by severity/status/category.
    Also used internally for /api/scans/{id}/findings/.
    """

    serializer_class = FindingListSerializer

    def get_queryset(self):
        qs = (
            Finding.objects.filter(scan__repository__owner=self.request.user)
            .select_related("rule", "scan", "scan__repository")
            .order_by("-severity", "-confidence_score")
        )
        # Filter by query params
        severity = self.request.query_params.get("severity")
        finding_status = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        file_path = self.request.query_params.get("file_path")
        scan_id = self.request.query_params.get("scan_id")
        source = self.request.query_params.get("source")

        if severity:
            qs = qs.filter(severity=severity)
        if finding_status:
            qs = qs.filter(status=finding_status)
        if category:
            qs = qs.filter(rule__category__icontains=category)
        if file_path:
            qs = qs.filter(file_path__icontains=file_path)
        if scan_id:
            qs = qs.filter(scan_id=scan_id)
        if source:
            qs = qs.filter(source=source)

        return qs

    @extend_schema(summary="List findings")
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})


class ScanFindingListView(FindingListView):
    """GET /api/scans/{scan_id}/findings/ — findings scoped to a specific scan."""

    def get_queryset(self):
        """Override queryset to scope findings to the URL-captured scan_id."""
        scan_id = self.kwargs["scan_id"]
        return (
            Finding.objects.filter(
                scan__id=scan_id,
                scan__repository__owner=self.request.user,
            )
            .select_related("rule", "scan", "scan__repository")
            .order_by("-severity_order", "file_path", "line_start")
        )


class FindingDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/findings/{id}/ — full finding detail.
    PATCH /api/findings/{id}/ — update triage status.
    """

    def get_queryset(self):
        return Finding.objects.filter(scan__repository__owner=self.request.user).select_related(
            "rule", "scan", "scan__repository", "suppressed_by"
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdateFindingStatusSerializer
        return FindingSerializer

    @extend_schema(summary="Get finding detail")
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({"success": True, "data": FindingSerializer(instance).data})

    @extend_schema(summary="Update finding status (triage)", request=UpdateFindingStatusSerializer)
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UpdateFindingStatusSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")

        # Record who suppressed the finding and when
        if new_status == FindingStatus.SUPPRESSED:
            instance.suppressed_by = request.user
            instance.suppressed_at = timezone.now()

        serializer.save()
        instance.refresh_from_db()
        return Response({"success": True, "data": FindingSerializer(instance).data})


class SimilarFindingsView(generics.ListAPIView):
    """GET /api/findings/{id}/similar/ — similar findings across other scans."""

    serializer_class = FindingListSerializer

    @extend_schema(summary="Find similar findings across scans")
    def list(self, request, pk, *args, **kwargs):
        target = Finding.objects.filter(
            scan__repository__owner=request.user, pk=pk
        ).select_related("rule").first()

        if not target:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Finding not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        similar = (
            Finding.objects.filter(
                scan__repository__owner=request.user,
                rule=target.rule,
            )
            .exclude(pk=target.pk)
            .select_related("rule", "scan", "scan__repository")
            .order_by("-created_at")[:20]
        )

        return Response({"success": True, "data": self.get_serializer(similar, many=True).data})
