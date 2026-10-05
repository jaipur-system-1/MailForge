"""MailForge URL configuration."""

from django.contrib import admin
from django.urls import include, path
from templates_api.views import EmailHistoryListCreateView

from .health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/history/", EmailHistoryListCreateView.as_view(), name="email-history"),
    path("api/templates/", include("templates_api.urls")),
]

