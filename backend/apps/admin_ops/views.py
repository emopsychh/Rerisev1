from decimal import InvalidOperation

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from apps.admin_ops.models import AuditLog
from apps.admin_ops.services import (
    AdminAdjustmentService,
    AuditLogger,
    UserModerationService,
)
from apps.ledger.constants import DIRECTION_CREDIT
from apps.ledger.services import LedgerError
from apps.users.models import User
from apps.wallet.constants import (
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_REJECTED,
)
from apps.wallet.models import WithdrawalRequest
from apps.wallet.services import WithdrawalService, WithdrawalValidationError
from core.responses import error_response, success_response


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AdminAdjustmentView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        amount = request.data.get("amount_usd")
        direction = request.data.get("direction", DIRECTION_CREDIT)
        reason = request.data.get("reason", "")

        user = get_object_or_404(User, pk=user_id)
        try:
            entry = AdminAdjustmentService.apply(
                user,
                amount_usd=amount,
                direction=direction,
                reason=reason,
                actor=request.user,
            )
        except (LedgerError, InvalidOperation, TypeError, ValueError) as exc:
            return error_response(
                "BUSINESS_RULE_ERROR",
                str(exc),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return success_response(
            {
                "entry_id": entry.pk,
                "user_id": user.pk,
                "direction": entry.direction,
                "amount_usd": float(entry.amount),
                "reason": reason,
            },
            status_code=status.HTTP_201_CREATED,
        )


class AdminBlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id: int):
        user = get_object_or_404(User, pk=user_id)
        if user.pk == request.user.pk:
            return error_response(
                "BUSINESS_RULE_ERROR",
                "Нельзя заблокировать себя",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        reason = request.data.get("reason", "")
        block = request.data.get("block", True)
        if block is False or str(block).lower() in {"false", "0", "unblock"}:
            UserModerationService.unblock(user, actor=request.user)
            action = "unblocked"
        else:
            UserModerationService.block(user, actor=request.user, reason=reason)
            action = "blocked"
        return success_response({"user_id": user.pk, "is_active": user.is_active, "action": action})


class AdminWithdrawalView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, withdrawal_id: int):
        withdrawal = get_object_or_404(WithdrawalRequest, pk=withdrawal_id)
        new_status = request.data.get("status")
        tx_hash = request.data.get("tx_hash", "")
        reason = request.data.get("reason", "")

        try:
            if new_status == WITHDRAWAL_STATUS_APPROVED:
                withdrawal = WithdrawalService.approve(withdrawal, reviewed_by=request.user)
            elif new_status == WITHDRAWAL_STATUS_REJECTED:
                withdrawal = WithdrawalService.reject(
                    withdrawal, reviewed_by=request.user, reason=reason
                )
            elif new_status == "paid":
                withdrawal = WithdrawalService.mark_paid(
                    withdrawal, reviewed_by=request.user, tx_hash=tx_hash
                )
            else:
                return error_response(
                    "VALIDATION_ERROR",
                    "status должен быть approved, rejected или paid",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        except WithdrawalValidationError as exc:
            return error_response(
                "BUSINESS_RULE_ERROR",
                str(exc),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        AuditLogger.record(
            actor=request.user,
            action=f"withdrawal_{new_status}",
            target_type="withdrawal_request",
            target_id=withdrawal.pk,
            new_value={"status": withdrawal.status, "tx_hash": withdrawal.tx_hash},
            ip_address=_client_ip(request),
        )
        return success_response(
            {
                "id": withdrawal.pk,
                "status": withdrawal.status,
                "amount_usd": float(withdrawal.amount_usd),
            }
        )


class AdminAuditLogView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = AuditLog.objects.select_related("actor").all()[:100]
        data = [
            {
                "id": row.pk,
                "action": row.action,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "actor_email": row.actor.email if row.actor_id else None,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "created_at": row.created_at.isoformat(),
            }
            for row in qs
        ]
        return success_response(data)
