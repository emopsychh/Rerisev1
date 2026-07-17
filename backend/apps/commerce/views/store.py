from rest_framework import permissions, status
from rest_framework.views import APIView

from apps.commerce.models import Order, Product
from apps.commerce.selectors import (
    get_active_tariff_products,
    get_order_for_user,
    serialize_create_order_response,
    serialize_order_detail,
    serialize_tariff_product,
    serialize_token_store,
)
from apps.commerce.serializers import CreateOrderSerializer
from apps.commerce.services import OrderService, OrderValidationError
from core.responses import error_response, success_response


class TariffListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = get_active_tariff_products()
        data = [serialize_tariff_product(product) for product in products]
        return success_response(data)


class TokenStoreView(APIView):
    def get(self, request):
        from apps.ibox.tokens import TokenService

        return success_response(
            serialize_token_store(balance=TokenService.get_available(request.user))
        )


class OrderCreateView(APIView):
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderService.create_order(
                user=request.user,
                product_slug=serializer.validated_data["product_id"],
                order_type=serializer.validated_data["order_type"],
            )
        except OrderValidationError as exc:
            return error_response(
                "BUSINESS_RULE_ERROR",
                str(exc),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Product.DoesNotExist:
            return error_response(
                "NOT_FOUND",
                "Продукт не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            serialize_create_order_response(order),
            status.HTTP_201_CREATED,
        )


class OrderDetailView(APIView):
    def get(self, request, order_id: int):
        try:
            order = get_order_for_user(order_id, request.user.id)
        except Order.DoesNotExist:
            return error_response(
                "NOT_FOUND",
                "Заказ не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(serialize_order_detail(order))
