from rest_framework import status
from rest_framework.views import APIView

from apps.commerce.models import Order, Product
from apps.commerce.selectors import serialize_create_order_response
from apps.commerce.services import OrderService, OrderValidationError
from apps.partner.dashboard import build_dashboard, build_ranks, build_structure
from apps.partner.selectors import (
    get_partner_profile,
    get_personal_invites,
    serialize_invited_partner,
)
from core.responses import error_response, success_response


class InvitedPartnersView(APIView):
    def get(self, request):
        partner = get_partner_profile(request.user.pk)
        if not partner:
            return success_response([])

        links = get_personal_invites(partner)
        data = [serialize_invited_partner(link) for link in links]
        return success_response(data)


class PartnerDashboardView(APIView):
    def get(self, request):
        return success_response(build_dashboard(request.user))


class PartnerRanksView(APIView):
    def get(self, request):
        partner = get_partner_profile(request.user.pk)
        if not partner:
            return success_response([])
        return success_response(build_ranks(partner))


class PartnerStructureView(APIView):
    def get(self, request):
        partner = get_partner_profile(request.user.pk)
        if not partner:
            return error_response(
                "NOT_FOUND",
                "Партнёрский профиль не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        leg = request.query_params.get("leg")
        try:
            depth = int(request.query_params.get("depth", 3))
        except (TypeError, ValueError):
            depth = 3
        from apps.commerce.selectors import get_tariff_caps

        caps = get_tariff_caps(partner.tariff_id) if partner.tariff_id else None
        max_depth = int(caps["binary_depth"]) if caps else 15
        depth = max(1, min(depth, max_depth))

        return success_response(build_structure(partner, leg=leg, depth=depth))


class PartnerRenewView(APIView):
    """Создаёт order на продление активности ($30 subscription)."""

    def post(self, request):
        try:
            order = OrderService.create_order(
                user=request.user,
                product_slug="subscription",
                order_type=Order.TYPE_RENEWAL,
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
                "Продукт продления не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response(
            serialize_create_order_response(order),
            status_code=status.HTTP_201_CREATED,
        )
