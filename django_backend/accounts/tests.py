from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    def test_health_check_reports_database_availability(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="sales.user",
            email="sales@example.com",
            password="test-password",
        )

    def test_login_current_user_and_logout(self):
        login = self.client.post(
            "/api/auth/login/",
            {"username": "sales.user", "password": "test-password"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        token = login.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        current_user = self.client.get("/api/auth/me/")
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.data["username"], "sales.user")
        self.assertFalse(current_user.data["is_superuser"])

        logout = self.client.post("/api/auth/logout/")
        self.assertEqual(logout.status_code, 204)

    def test_login_accepts_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "sales@example.com", "password": "test-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "sales.user", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class AdminUserCreateApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.superuser = get_user_model().objects.create_superuser(
            username="super.admin",
            email="admin@example.com",
            password="test-password",
        )
        token = Token.objects.create(user=self.superuser)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def user_payload(self):
        return {
            "username": "new.employee",
            "email": "employee@example.com",
            "first_name": "New",
            "last_name": "Employee",
            "password": "secure-password",
            "groups": ["sales"],
        }

    def test_superuser_can_list_create_and_delete_grouped_employee(self):
        response = self.client.post(
            "/api/auth/admin/users/",
            self.user_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        created = get_user_model().objects.get(username="new.employee")
        self.assertTrue(created.check_password("secure-password"))
        self.assertFalse(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertEqual(
            list(created.groups.values_list("name", flat=True)),
            ["sales"],
        )

        listed = self.client.get("/api/auth/admin/users/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data["users"]), 2)

        deleted = self.client.delete(f"/api/auth/admin/users/{created.pk}/")
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(
            get_user_model().objects.filter(username="new.employee").exists()
        )

    def test_superuser_cannot_delete_own_account(self):
        response = self.client.delete(
            f"/api/auth/admin/users/{self.superuser.pk}/"
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            get_user_model().objects.filter(pk=self.superuser.pk).exists()
        )

    def test_non_superuser_cannot_create_users(self):
        employee = get_user_model().objects.create_user(
            username="ordinary.employee",
            password="test-password",
        )
        token = Token.objects.create(user=employee)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(
            "/api/auth/admin/users/",
            self.user_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            get_user_model().objects.filter(username="new.employee").exists()
        )
