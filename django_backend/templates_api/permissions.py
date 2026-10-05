"""Check template allowed_groups against the authenticated user."""

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Allow template-source management only for active superusers."""

    message = "Super Admin access is required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user.is_authenticated and user.is_active and user.is_superuser)


def user_can_access_template(user, template: dict) -> bool:
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or user.is_staff:
        return True

    allowed_groups = set(template.get("allowed_groups", []))
    if not allowed_groups:
        return True

    user_groups = set(user.groups.values_list("name", flat=True))
    return bool(user_groups & allowed_groups)

