from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.ledger.constants import (
    CURRENCY_USD,
    DEBT_STATUS_OPEN,
    DIRECTION_CREDIT,
    DIRECTION_DEBIT,
    ENTRY_TYPE_WITHDRAWAL,
)
from apps.ledger.models import AdjustmentDebt, Entry
from apps.ledger.selectors import get_active_rule_version
from apps.ledger.services import LedgerWriter
from apps.users.models import User
from apps.wallet.constants import (
    DEFAULT_WITHDRAWAL_MAX_PER_REQUEST_USD,
    DEFAULT_WITHDRAWAL_MIN_USD,
    PENDING_WITHDRAWAL_STATUSES,
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_PAID,
    WITHDRAWAL_STATUS_PENDING,
    WITHDRAWAL_STATUS_REJECTED,
)
from apps.wallet.models import Balance, WithdrawalRequest


class WalletUpdater:
    @staticmethod
    def _calculate(user_id: int) -> dict[str, Decimal]:
        credits = (
            Entry.objects.filter(
                user_id=user_id,
                currency=CURRENCY_USD,
                direction=DIRECTION_CREDIT,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

        debits = (
            Entry.objects.filter(
                user_id=user_id,
                currency=CURRENCY_USD,
                direction=DIRECTION_DEBIT,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

        net = credits - debits

        pending = (
            WithdrawalRequest.objects.filter(
                user_id=user_id,
                status__in=PENDING_WITHDRAWAL_STATUSES,
            ).aggregate(total=Sum("amount_usd"))["total"]
            or Decimal("0")
        )

        debt = (
            AdjustmentDebt.objects.filter(
                user_id=user_id,
                status=DEBT_STATUS_OPEN,
            ).aggregate(total=Sum("remaining_usd"))["total"]
            or Decimal("0")
        )

        return {
            "available_usd": max(net - pending - debt, Decimal("0")),
            "pending_usd": pending,
            "total_earned_usd": credits,
        }

    @staticmethod
    @transaction.atomic
    def refresh(user: User, *, locked_balance: Balance | None = None) -> Balance:
        amounts = WalletUpdater._calculate(user.pk)

        if locked_balance is not None:
            balance = locked_balance
        else:
            balance, _ = Balance.objects.get_or_create(user=user)

        balance.available_usd = amounts["available_usd"]
        balance.pending_usd = amounts["pending_usd"]
        balance.total_earned_usd = amounts["total_earned_usd"]
        balance.save(
            update_fields=["available_usd", "pending_usd", "total_earned_usd", "updated_at"]
        )
        return balance


class WithdrawalValidationError(ValueError):
    pass


class WithdrawalService:
    @staticmethod
    @transaction.atomic
    def create_request(
        user: User,
        amount_usd: Decimal | int | float | str,
        usdt_address: str,
        network: str,
        *,
        limits: dict | None = None,
    ) -> WithdrawalRequest:
        normalized_amount = Decimal(str(amount_usd))
        limits = limits or {}
        min_usd = Decimal(str(limits.get("min_usd", DEFAULT_WITHDRAWAL_MIN_USD)))
        max_usd = Decimal(
            str(limits.get("max_per_request_usd", DEFAULT_WITHDRAWAL_MAX_PER_REQUEST_USD))
        )

        if normalized_amount < min_usd:
            raise WithdrawalValidationError(f"Минимальная сумма вывода — ${min_usd}")
        if normalized_amount > max_usd:
            raise WithdrawalValidationError(f"Максимальная сумма за одну заявку — ${max_usd}")

        address = usdt_address.strip()
        if not address:
            raise WithdrawalValidationError("USDT-адрес не может быть пустым")

        balance, _ = Balance.objects.select_for_update().get_or_create(user=user)
        WalletUpdater.refresh(user, locked_balance=balance)

        if normalized_amount > balance.available_usd:
            raise WithdrawalValidationError("Недостаточно средств на балансе")

        request = WithdrawalRequest.objects.create(
            user=user,
            amount_usd=normalized_amount,
            usdt_address=address,
            network=network,
        )
        SavedAddressService.save_default(user, address, network)
        WalletUpdater.refresh(user, locked_balance=balance)
        return request

    @staticmethod
    @transaction.atomic
    def approve(
        request: WithdrawalRequest,
        reviewed_by: User,
    ) -> WithdrawalRequest:
        request = WithdrawalRequest.objects.select_for_update().get(pk=request.pk)
        if request.status == WITHDRAWAL_STATUS_APPROVED:
            return request
        if request.status == WITHDRAWAL_STATUS_PAID:
            raise WithdrawalValidationError("Заявка уже выплачена")
        if request.status == WITHDRAWAL_STATUS_REJECTED:
            raise WithdrawalValidationError("Заявка уже отклонена")
        if request.status != WITHDRAWAL_STATUS_PENDING:
            raise WithdrawalValidationError("Можно одобрить только pending-заявку")

        request.status = WITHDRAWAL_STATUS_APPROVED
        request.reviewed_by = reviewed_by
        request.save(update_fields=["status", "reviewed_by", "updated_at"])
        return request

    @staticmethod
    @transaction.atomic
    def reject(
        request: WithdrawalRequest,
        reviewed_by: User,
        *,
        reason: str = "",
    ) -> WithdrawalRequest:
        request = WithdrawalRequest.objects.select_for_update().get(pk=request.pk)
        if request.status == WITHDRAWAL_STATUS_REJECTED:
            return request
        if request.status == WITHDRAWAL_STATUS_PAID:
            raise WithdrawalValidationError("Заявка уже выплачена")

        request.status = WITHDRAWAL_STATUS_REJECTED
        request.reviewed_by = reviewed_by
        request.rejection_reason = reason.strip() or None
        request.save(
            update_fields=["status", "reviewed_by", "rejection_reason", "updated_at"]
        )
        WalletUpdater.refresh(request.user)
        return request

    @staticmethod
    @transaction.atomic
    def mark_paid(
        request: WithdrawalRequest,
        reviewed_by: User,
        *,
        tx_hash: str = "",
    ) -> WithdrawalRequest:
        request = WithdrawalRequest.objects.select_for_update().get(pk=request.pk)
        if request.status == WITHDRAWAL_STATUS_PAID:
            return request
        if request.status == WITHDRAWAL_STATUS_REJECTED:
            raise WithdrawalValidationError("Заявка уже отклонена")
        if request.status not in (WITHDRAWAL_STATUS_PENDING, WITHDRAWAL_STATUS_APPROVED):
            raise WithdrawalValidationError("Нельзя выплатить заявку в текущем статусе")

        LedgerWriter.debit(
            request.user,
            ENTRY_TYPE_WITHDRAWAL,
            request.amount_usd,
            source=request,
            idempotency_key=f"withdrawal:{request.id}:paid",
            description=f"Вывод USDT #{request.id}",
        )

        request.status = WITHDRAWAL_STATUS_PAID
        request.reviewed_by = reviewed_by
        request.tx_hash = tx_hash or None
        request.paid_at = timezone.now()
        request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "tx_hash",
                "paid_at",
                "updated_at",
            ]
        )
        WalletUpdater.refresh(request.user)
        return request


class SavedAddressService:
    @staticmethod
    @transaction.atomic
    def save_default(user: User, address: str, network: str):
        from apps.wallet.models import SavedAddress

        SavedAddress.objects.filter(user=user).update(is_default=False)
        saved, _ = SavedAddress.objects.update_or_create(
            user=user,
            network=network,
            defaults={"address": address.strip(), "is_default": True},
        )
        return saved
