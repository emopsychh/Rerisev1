from django.urls import path

from apps.commerce.views.store import (
    OrderCreateView,
    OrderDetailView,
    TariffListView,
    TokenStoreView,
)
from apps.commerce.views.webhook import cryptobot_webhook

urlpatterns = [
    path("store/tariffs", TariffListView.as_view(), name="store-tariffs"),
    path("store/tokens", TokenStoreView.as_view(), name="store-tokens"),
    path("store/orders", OrderCreateView.as_view(), name="store-orders-create"),
    path("store/orders/<int:order_id>", OrderDetailView.as_view(), name="store-orders-detail"),
    path(
        "store/webhook/cryptobot/<str:secret_path>",
        cryptobot_webhook,
        name="store-webhook-cryptobot",
    ),
]
