from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from pathlib import Path
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
import shutil

from .repository import TemplateRepository


class TemplateRepositoryTests(TestCase):
    def test_registry_returns_active_templates_with_field_count(self):
        templates = TemplateRepository().list_templates()
        gmc = next(template for template in templates if template["id"] == "gmc_proposal")
        self.assertEqual(gmc["field_count"], 4)


class TemplateListApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="template.user",
            password="test-password",
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_user_without_allowed_group_gets_empty_library(self):
        response = self.client.get("/api/templates/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["templates"], [])

    def test_sales_user_gets_gmc_template(self):
        sales = Group.objects.create(name="sales")
        self.user.groups.add(sales)

        response = self.client.get("/api/templates/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["templates"]), 1)
        self.assertEqual(response.data["templates"][0]["id"], "gmc_proposal")

    def test_sales_user_can_load_fields_and_render_safe_preview(self):
        sales = Group.objects.create(name="sales")
        self.user.groups.add(sales)

        detail = self.client.get("/api/templates/gmc_proposal/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.data["fields"]), 4)

        preview = self.client.post(
            "/api/templates/gmc_proposal/render/",
            {
                "values": {
                    "company_name": "Example <script>alert(1)</script>",
                    "recipient_greeting": "Dear {{ company_name }} Team,",
                    "proposal_message": "First paragraph.\n\nSecond paragraph.",
                    "closing_message": "We look forward to working with {{ company_name }}.",
                }
            },
            format="json",
        )

        self.assertEqual(preview.status_code, 200)
        self.assertNotIn("<script>alert(1)</script>", preview.data["html"])
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", preview.data["html"])
        self.assertIn("First paragraph.<br>\n<br>\nSecond paragraph.", preview.data["html"])

    def test_staff_user_can_access_all_active_templates(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        response = self.client.get("/api/templates/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["templates"]), 1)


class EmailHistoryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="history.user",
            password="test-password",
        )
        self.user.groups.add(Group.objects.create(name="sales"))
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def history_payload(self):
        return {
            "template_id": "gmc_proposal",
            "recipient_company": "Example Industries",
        }

    def test_user_can_record_and_list_own_inserted_email(self):
        created = self.client.post(
            "/api/history/",
            self.history_payload(),
            format="json",
        )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["template_name"], "GMC Business Proposal")
        self.assertEqual(created.data["recipient_company"], "Example Industries")
        self.assertNotIn("rendered_html", created.data)

        listed = self.client.get("/api/history/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data["history"]), 1)
        self.assertEqual(listed.data["history"][0]["id"], created.data["id"])

    def test_history_is_private_to_the_authenticated_user(self):
        self.client.post("/api/history/", self.history_payload(), format="json")
        other = get_user_model().objects.create_user(
            username="other.history.user",
            password="test-password",
        )
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        listed = self.client.get("/api/history/")

        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["history"], [])


class AdminTemplateApiTests(TestCase):
    def setUp(self):
        self.template_root = (
            Path(settings.PROJECT_DIR)
            / "test_artifacts"
            / self._testMethodName
        )
        shutil.rmtree(self.template_root, ignore_errors=True)
        self.template_root.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(self.template_root, ignore_errors=True))
        (self.template_root / "templates.json").write_text("[]\n", encoding="utf-8")
        self.settings_override = override_settings(
            EMAIL_TEMPLATE_ROOT=self.template_root
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.client = APIClient()
        self.superuser = get_user_model().objects.create_superuser(
            username="super.admin",
            password="test-password",
        )
        token = Token.objects.create(user=self.superuser)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def template_payload(self):
        return {
            "id": "welcome_email",
            "name": "Welcome Email",
            "description": "New employee welcome message",
            "allowed_groups": ["sales"],
            "active": True,
            "fields": [
                {
                    "name": "recipient_greeting",
                    "label": "Greeting",
                    "type": "text",
                    "required": True,
                    "default": "Dear Team,",
                    "max_length": 250,
                }
            ],
            "html": "<html><body><p>{{ recipient_greeting }}</p></body></html>",
        }

    def test_superuser_can_create_update_and_delete_template_source(self):
        created = self.client.post(
            "/api/templates/admin/",
            self.template_payload(),
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertTrue(
            (self.template_root / "welcome_email" / "template.html").is_file()
        )

        payload = self.template_payload()
        payload["name"] = "Updated Welcome Email"
        updated = self.client.put(
            "/api/templates/admin/welcome_email/",
            payload,
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["name"], "Updated Welcome Email")

        deleted = self.client.delete(
            "/api/templates/admin/welcome_email/"
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(
            (self.template_root / "welcome_email").exists()
        )
        self.assertEqual(
            list((self.template_root / ".trash").iterdir())[0].name.startswith(
                "welcome_email-"
            ),
            True,
        )

    def test_non_superuser_cannot_manage_template_source(self):
        employee = get_user_model().objects.create_user(
            username="employee",
            password="test-password",
            is_staff=True,
        )
        token = Token.objects.create(user=employee)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(
            "/api/templates/admin/",
            self.template_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 403)

