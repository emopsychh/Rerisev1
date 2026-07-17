from rest_framework import status
from rest_framework.views import APIView

from apps.wallet.constants import TRANSACTION_FILTER_ALL, TRANSACTION_FILTER_CHOICES
from apps.wallet.selectors import (
    get_active_withdrawal_limits,
    get_transaction_queryset,
    get_wallet_overview,
    serialize_saved_address,
    serialize_transaction,
    serialize_withdrawal_request,
)
from apps.wallet.serializers import SaveAddressSerializer, WithdrawSerializer
from apps.wallet.services import SavedAddressService, WithdrawalService, WithdrawalValidationError
from core.pagination import StandardPagination
from core.responses import error_response, success_response


class WalletOverviewView(APIView):
    def get(self, request):
        return success_response(get_wallet_overview(request.user))


class WalletTransactionsView(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        entry_type = request.query_params.get("type", TRANSACTION_FILTER_ALL)
        if entry_type not in TRANSACTION_FILTER_CHOICES:
            entry_type = TRANSACTION_FILTER_ALL

        period = request.query_params.get("period")
        queryset = get_transaction_queryset(
            request.user,
            entry_type=entry_type,
            period=period,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [serialize_transaction(entry) for entry in page]
        return paginator.get_paginated_response(data)


class WalletWithdrawView(APIView):
    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            withdrawal = WithdrawalService.create_request(
                user=request.user,
                amount_usd=serializer.validated_data["amount_usd"],
                usdt_address=serializer.validated_data["usdt_address"],
                network=serializer.validated_data["network"],
                limits=get_active_withdrawal_limits(),
            )
        except WithdrawalValidationError as exc:
            return error_response(
                "BUSINESS_RULE_ERROR",
                str(exc),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return success_response(
            serialize_withdrawal_request(withdrawal),
            status.HTTP_201_CREATED,
        )


class WalletAddressView(APIView):
    def put(self, request):
        serializer = SaveAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        saved = SavedAddressService.save_default(
            user=request.user,
            address=serializer.validated_data["address"],
            network=serializer.validated_data["network"],
        )
        return success_response(serialize_saved_address(saved))
