"""URL patterns for the scans app."""
from django.urls import path

from .views import CancelScanView, ScanDetailView, ScanListView, TriggerScanView

urlpatterns = [
    path("", ScanListView.as_view(), name="scan-list"),
    path("<uuid:pk>/", ScanDetailView.as_view(), name="scan-detail"),
    path("<uuid:pk>/cancel/", CancelScanView.as_view(), name="scan-cancel"),
]

# Additional route mounted under repositories — see repositories/urls.py
scan_trigger_urlpatterns = [
    path("<uuid:repo_pk>/scans/", TriggerScanView.as_view(), name="scan-trigger"),
]
