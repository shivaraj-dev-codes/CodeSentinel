"""URL patterns for the analytics app."""
from django.urls import path

from .views import (
    DashboardOverviewView,
    FixRateView,
    RepositoryHealthView,
    SeverityTrendView,
    TopVulnerabilityCategoriesView,
)

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="analytics-overview"),
    path("severity-trend/", SeverityTrendView.as_view(), name="analytics-severity-trend"),
    path("top-vulnerability-categories/", TopVulnerabilityCategoriesView.as_view(), name="analytics-categories"),
    path("repository-health/", RepositoryHealthView.as_view(), name="analytics-repo-health"),
    path("fix-rate/", FixRateView.as_view(), name="analytics-fix-rate"),
]
