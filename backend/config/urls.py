import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.media import serve_media_with_range

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.commerce.urls")),
    path("api/v1/", include("apps.partner.urls")),
    path("api/v1/", include("apps.wallet.urls")),
    path("api/v1/", include("apps.academy.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.ibox.urls")),
    path("api/v1/", include("apps.crm.urls")),
    path("api/v1/", include("apps.admin_ops.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

# In production nginx serves /media/; keep Django fallback for local / single-container.
if settings.DEBUG or os.getenv("DJANGO_SERVE_MEDIA", "false").lower() == "true":
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve_media_with_range,
            name="media-with-range",
        ),
    ]
