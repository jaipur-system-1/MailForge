"""Account-management permissions."""

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Allow user administration only for active superusers."""

    message = "Super Admin access is required."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user.is_authenticated and user.is_active and user.is_superuser)
