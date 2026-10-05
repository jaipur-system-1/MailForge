"""Template library and render API views."""

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .permissions import IsSuperAdmin, user_can_access_template
from .models import EmailHistory
from .renderer import TemplateRenderError, render_template
from .repository import TemplateRepository, TemplateRepositoryError
from .serializers import (
    RenderTemplateSerializer,
    EmailHistoryCreateSerializer,
    EmailHistorySerializer,
    TemplateAdminSerializer,
    TemplateAdminSummarySerializer,
    TemplateDetailSerializer,
    TemplateSummarySerializer,
)


class EmailHistoryListCreateView(APIView):
    def get(self, request):
        entries = EmailHistory.objects.filter(user=request.user)
        return Response({"history": EmailHistorySerializer(entries, many=True).data})

    def post(self, request):
        serializer = EmailHistoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            template = TemplateRepository().get_template(data["template_id"])
        except TemplateRepositoryError:
            template = None
        if template is None or not user_can_access_template(request.user, template):
            return Response(
                {"detail": "Template not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        entry = EmailHistory.objects.create(
            user=request.user,
            template_id=template["id"],
            template_name=template["name"],
            recipient_company=data["recipient_company"].strip(),
        )
        return Response(
            EmailHistorySerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )


class TemplateListView(APIView):
    def get(self, request):
        templates = [
            template
            for template in TemplateRepository().list_templates()
            if user_can_access_template(request.user, template)
        ]
        serializer = TemplateSummarySerializer(templates, many=True)
        return Response({"templates": serializer.data})


class TemplateDetailView(APIView):
    def get_template(self, request, template_id):
        try:
            template = TemplateRepository().get_template(template_id)
        except TemplateRepositoryError:
            return None
        if not user_can_access_template(request.user, template):
            return None
        return template

    def get(self, request, template_id):
        template = self.get_template(request, template_id)
        if template is None:
            return Response(
                {"detail": "Template not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TemplateDetailSerializer(template).data)


class TemplateRenderView(TemplateDetailView):
    def post(self, request, template_id):
        template = self.get_template(request, template_id)
        if template is None:
            return Response(
                {"detail": "Template not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RenderTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rendered_html = render_template(template, serializer.validated_data["values"])
        except TemplateRenderError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "template": TemplateSummarySerializer(template).data,
                "html": rendered_html,
            }
        )


class AdminTemplateListCreateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        templates = TemplateRepository().list_templates(include_inactive=True)
        return Response(
            {"templates": TemplateAdminSummarySerializer(templates, many=True).data}
        )

    def post(self, request):
        serializer = TemplateAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            template = TemplateRepository().create_template(serializer.validated_data)
        except TemplateRepositoryError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TemplateAdminSerializer(template).data, status=status.HTTP_201_CREATED)


class AdminTemplateDetailView(APIView):
    permission_classes = [IsSuperAdmin]

    def get_template(self, template_id):
        try:
            return TemplateRepository().get_template(
                template_id,
                include_inactive=True,
            )
        except TemplateRepositoryError:
            return None

    def get(self, request, template_id):
        template = self.get_template(template_id)
        if template is None:
            return Response(
                {"detail": "Template not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(TemplateAdminSerializer(template).data)

    def put(self, request, template_id):
        serializer = TemplateAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            template = TemplateRepository().update_template(
                template_id,
                serializer.validated_data,
            )
        except TemplateRepositoryError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TemplateAdminSerializer(template).data)

    def delete(self, request, template_id):
        try:
            TemplateRepository().delete_template(template_id)
        except TemplateRepositoryError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

