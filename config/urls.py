"""Root URL configuration for CodeSentinel."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API routes
    path("api/auth/", include("apps.users.urls")),
    path("api/repositories/", include("apps.repositories.urls")),
    path("api/scans/", include("apps.scans.urls")),
    path("api/findings/", include("apps.findings.urls")),
    path("api/analytics/", include("apps.analytics.urls")),

    # Auto-generated API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
