from django.urls import path

from .views import (
    AdminUserDetailView,
    AdminUserListCreateView,
    CurrentUserView,
    LoginView,
    LogoutView,
)


urlpatterns = [
    path("admin/users/", AdminUserListCreateView.as_view(), name="admin-user-list"),
    path(
        "admin/users/<int:user_id>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]

