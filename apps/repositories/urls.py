"""URL patterns for the repositories app."""
from django.urls import path

from apps.scans.urls import scan_trigger_urlpatterns
from .views import GitHubRepoListView, RepositoryDetailView, RepositoryListCreateView

urlpatterns = [
    path("", RepositoryListCreateView.as_view(), name="repository-list"),
    path("github/", GitHubRepoListView.as_view(), name="repository-github-list"),
    path("<uuid:pk>/", RepositoryDetailView.as_view(), name="repository-detail"),
    # Nested: POST /api/repositories/<repo_pk>/scans/ triggers a scan
    *scan_trigger_urlpatterns,
]
