"""CRUD views for connected GitHub repositories."""
import requests
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Repository
from .serializers import AddRepositorySerializer, GitHubRepoSerializer, RepositorySerializer


class RepositoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/repositories/  — list the current user's connected repositories.
    POST /api/repositories/  — add a new repository by GitHub full_name.
    """

    serializer_class = RepositorySerializer

    def get_queryset(self):
        return Repository.objects.filter(owner=self.request.user).prefetch_related("scans")

    @extend_schema(summary="List connected repositories")
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="Add a repository", request=AddRepositorySerializer)
    def create(self, request, *args, **kwargs):
        serializer = AddRepositorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        full_name = serializer.validated_data["full_name"]

        if not request.user.has_github_connected:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "GITHUB_NOT_CONNECTED",
                        "message": "Connect your GitHub account before adding repositories.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch repo metadata from GitHub
        try:
            gh_resp = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers={
                    "Authorization": f"token {request.user.github_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10,
            )
            gh_resp.raise_for_status()
            gh_data = gh_resp.json()
        except requests.HTTPError as exc:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "GITHUB_API_ERROR",
                        "message": f"GitHub returned {exc.response.status_code}. "
                        "Check the repository name and your access permissions.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        repo, created = Repository.objects.get_or_create(
            owner=request.user,
            github_repo_id=gh_data["id"],
            defaults={
                "name": gh_data["name"],
                "full_name": gh_data["full_name"],
                "github_repo_url": gh_data["html_url"],
                "clone_url": gh_data["clone_url"],
                "default_branch": gh_data.get("default_branch", "main"),
                "description": gh_data.get("description") or "",
                "is_private": gh_data.get("private", False),
                "language": gh_data.get("language") or "",
            },
        )

        if not created:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ALREADY_CONNECTED",
                        "message": "This repository is already connected.",
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {"success": True, "data": RepositorySerializer(repo).data},
            status=status.HTTP_201_CREATED,
        )


class RepositoryDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/repositories/{id}/  — repository detail with scan history.
    DELETE /api/repositories/{id}/  — remove the repository.
    """

    serializer_class = RepositorySerializer

    def get_queryset(self):
        return Repository.objects.filter(owner=self.request.user)

    @extend_schema(summary="Get repository detail")
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="Remove a connected repository")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "data": {"message": "Repository removed."}})


class GitHubRepoListView(APIView):
    """
    GET /api/repositories/github/
    Return all GitHub repos the user has access to,
    annotated with whether each one is already connected.
    """

    @extend_schema(summary="List available GitHub repositories")
    def get(self, request):
        if not request.user.has_github_connected:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "GITHUB_NOT_CONNECTED",
                        "message": "Connect your GitHub account first.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            gh_resp = requests.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {request.user.github_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"per_page": 100, "sort": "updated", "type": "all"},
                timeout=10,
            )
            gh_resp.raise_for_status()
            repos = gh_resp.json()
        except requests.HTTPError:
            return Response(
                {
                    "success": False,
                    "error": {"code": "GITHUB_API_ERROR", "message": "Failed to fetch repos from GitHub."},
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        connected_ids = set(
            Repository.objects.filter(owner=request.user).values_list("github_repo_id", flat=True)
        )

        data = [
            {
                "id": r["id"],
                "name": r["name"],
                "full_name": r["full_name"],
                "html_url": r["html_url"],
                "clone_url": r["clone_url"],
                "default_branch": r.get("default_branch", "main"),
                "description": r.get("description"),
                "private": r.get("private", False),
                "language": r.get("language"),
                "already_connected": r["id"] in connected_ids,
            }
            for r in repos
        ]

        return Response({"success": True, "data": data})
