from django.urls import path

from apps.ibox.views import (
    ScenarioListView,
    SessionDetailView,
    SessionListCreateView,
    SessionMessageView,
)

urlpatterns = [
    path("ibox/scenarios", ScenarioListView.as_view(), name="ibox-scenarios"),
    path("ibox/sessions", SessionListCreateView.as_view(), name="ibox-sessions"),
    path(
        "ibox/sessions/<int:session_id>",
        SessionDetailView.as_view(),
        name="ibox-session-detail",
    ),
    path(
        "ibox/sessions/<int:session_id>/messages",
        SessionMessageView.as_view(),
        name="ibox-session-messages",
    ),
]
