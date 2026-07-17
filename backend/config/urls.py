from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
