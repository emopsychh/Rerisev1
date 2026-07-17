from django.urls import path

from apps.content.views import (
    ChatsView,
    HomeView,
    MaterialFileDownloadView,
    MaterialGroupDetailView,
    MaterialsCatalogView,
)

urlpatterns = [
    path("home", HomeView.as_view(), name="home"),
    path("materials", MaterialsCatalogView.as_view(), name="materials"),
    path(
        "materials/groups/<int:group_id>",
        MaterialGroupDetailView.as_view(),
        name="materials-group",
    ),
    path(
        "materials/files/<int:file_id>/download",
        MaterialFileDownloadView.as_view(),
        name="materials-file-download",
    ),
    path("chats", ChatsView.as_view(), name="chats"),
]
