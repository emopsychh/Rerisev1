from django.urls import path

from apps.users.views import (
    InviteLinkView,
    LoginView,
    MeProfileView,
    MeSummaryView,
    MeView,
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationSettingsView,
    RefreshView,
    RegisterView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("me", MeView.as_view(), name="me"),
    path("me/summary", MeSummaryView.as_view(), name="me-summary"),
    path("me/profile", MeProfileView.as_view(), name="me-profile"),
    path("me/invite-link", InviteLinkView.as_view(), name="me-invite-link"),
    path(
        "me/notifications",
        NotificationSettingsView.as_view(),
        name="me-notifications-settings",
    ),
    path("notifications", NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/read-all",
        NotificationReadAllView.as_view(),
        name="notifications-read-all",
    ),
    path(
        "notifications/<int:pk>/read",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
]
