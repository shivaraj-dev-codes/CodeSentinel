"""URL patterns for the findings app."""
from django.urls import path

from .views import FindingDetailView, FindingListView, SimilarFindingsView

urlpatterns = [
    path("", FindingListView.as_view(), name="finding-list"),
    path("<uuid:pk>/", FindingDetailView.as_view(), name="finding-detail"),
    path("<uuid:pk>/similar/", SimilarFindingsView.as_view(), name="finding-similar"),
]
