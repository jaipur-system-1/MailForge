from django.urls import path

from .views import (
    AdminTemplateDetailView,
    AdminTemplateListCreateView,
    TemplateDetailView,
    TemplateListView,
    TemplateRenderView,
)


urlpatterns = [
    path("admin/", AdminTemplateListCreateView.as_view(), name="admin-template-list"),
    path(
        "admin/<str:template_id>/",
        AdminTemplateDetailView.as_view(),
        name="admin-template-detail",
    ),
    path("", TemplateListView.as_view(), name="template-list"),
    path("<str:template_id>/", TemplateDetailView.as_view(), name="template-detail"),
    path(
        "<str:template_id>/render/",
        TemplateRenderView.as_view(),
        name="template-render",
    ),
]

