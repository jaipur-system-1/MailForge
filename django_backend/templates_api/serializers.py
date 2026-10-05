"""Template listing and rendering serializers."""

import re

from jinja2 import Environment, TemplateSyntaxError, meta
from rest_framework import serializers

from .models import EmailHistory


class TemplateSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    allowed_groups = serializers.ListField(child=serializers.CharField())
    field_count = serializers.IntegerField()


class EditableFieldSerializer(serializers.Serializer):
    name = serializers.RegexField(r"^[A-Za-z_][A-Za-z0-9_]*$", max_length=64)
    label = serializers.CharField(max_length=150)
    type = serializers.ChoiceField(choices=["text", "textarea"])
    required = serializers.BooleanField(default=False)
    default = serializers.CharField(required=False, allow_blank=True)
    max_length = serializers.IntegerField(required=False, min_value=1, max_value=10000)


class TemplateDetailSerializer(TemplateSummarySerializer):
    fields = EditableFieldSerializer(many=True)


class TemplateAdminSummarySerializer(TemplateSummarySerializer):
    active = serializers.BooleanField()


class RenderTemplateSerializer(serializers.Serializer):
    values = serializers.DictField(child=serializers.CharField(allow_blank=True))


class EmailHistoryCreateSerializer(serializers.Serializer):
    template_id = serializers.RegexField(r"^[a-z0-9][a-z0-9_-]{1,63}$")
    recipient_company = serializers.CharField(max_length=150)


class EmailHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailHistory
        fields = [
            "id",
            "template_id",
            "template_name",
            "recipient_company",
            "inserted_at",
        ]
        read_only_fields = fields


class TemplateAdminSerializer(serializers.Serializer):
    id = serializers.RegexField(r"^[a-z0-9][a-z0-9_-]{1,63}$")
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
    )
    allowed_groups = serializers.ListField(
        child=serializers.CharField(max_length=150),
        allow_empty=True,
    )
    active = serializers.BooleanField(default=True)
    fields = EditableFieldSerializer(many=True, allow_empty=False, max_length=50)
    html = serializers.CharField(trim_whitespace=False, max_length=500000)

    def validate(self, attrs):
        field_names = [field["name"] for field in attrs["fields"]]
        if len(field_names) != len(set(field_names)):
            raise serializers.ValidationError(
                {"fields": "Editable field names must be unique."}
            )

        html = attrs["html"]
        if not re.search(r"<html(?:\s|>)", html, flags=re.IGNORECASE):
            raise serializers.ValidationError(
                {"html": "Provide a complete HTML document containing an <html> tag."}
            )

        environment = Environment()
        try:
            parsed = environment.parse(html)
        except TemplateSyntaxError as exc:
            raise serializers.ValidationError(
                {"html": f"Invalid template syntax: {exc.message}"}
            ) from exc

        unknown_variables = meta.find_undeclared_variables(parsed) - set(field_names)
        if unknown_variables:
            names = ", ".join(sorted(unknown_variables))
            raise serializers.ValidationError(
                {"html": f"Unknown editable field placeholders: {names}."}
            )

        attrs["allowed_groups"] = list(dict.fromkeys(attrs["allowed_groups"]))
        return attrs

