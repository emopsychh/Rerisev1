from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.admin_ops.models import AuditLog
from apps.ledger.constants import (
    CURRENCY_USD,
    DIRECTION_CREDIT,
    DIRECTION_DEBIT,
    ENTRY_TYPE_ADJUSTMENT,
)
from apps.ledger.models import AdjustmentDebt
from apps.ledger.services import AdjustmentService, LedgerError, LedgerWriter
from apps.users.models import User
from apps.wallet.models import Balance
from apps.wallet.services import WalletUpdater


class AuditLogger:
    @staticmethod
    def record(
        *,
        actor: User | None,
        action: str,
        target_type: str,
        target_id: int | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )


class UserModerationService:
    @staticmethod
    @transaction.atomic
    def block(user: User, *, actor: User, reason: str = "") -> User:
        if not user.is_active:
            return user
        old = {"is_active": True}
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        AuditLogger.record(
            actor=actor,
            action="user_blocked",
            target_type="user",
            target_id=user.pk,
            old_value=old,
            new_value={"is_active": False, "reason": reason},
        )
        return user

    @staticmethod
    @transaction.atomic
    def unblock(user: User, *, actor: User) -> User:
        if user.is_active:
            return user
        old = {"is_active": False}
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        AuditLogger.record(
            actor=actor,
            action="user_unblocked",
            target_type="user",
            target_id=user.pk,
            old_value=old,
            new_value={"is_active": True},
        )
        return user


class AdminAdjustmentService:
    """Ручные USD-корректировки из админки / staff API."""

    @staticmethod
    @transaction.atomic
    def apply(
        user: User,
        *,
        amount_usd: Decimal | int | float | str,
        direction: str,
        reason: str,
        actor: User,
    ):
        normalized = Decimal(str(amount_usd))
        if normalized <= 0:
            raise LedgerError("Сумма корректировки должна быть больше нуля")
        if direction not in (DIRECTION_CREDIT, DIRECTION_DEBIT):
            raise LedgerError("direction должен быть credit или debit")
        if not reason.strip():
            raise LedgerError("Укажите причину корректировки")

        writer = LedgerWriter.credit if direction == DIRECTION_CREDIT else LedgerWriter.debit
        if direction == DIRECTION_DEBIT:
            balance, _ = Balance.objects.select_for_update().get_or_create(user=user)
            WalletUpdater.refresh(user, locked_balance=balance)
            if normalized > balance.available_usd:
                raise LedgerError(
                    f"Недостаточно средств для debit-корректировки "
                    f"(доступно ${balance.available_usd})"
                )

        entry = writer(
            user,
            ENTRY_TYPE_ADJUSTMENT,
            normalized,
            currency=CURRENCY_USD,
            source=actor,
            description=reason.strip(),
            metadata={"reason": reason.strip(), "admin_id": actor.pk},
            idempotency_key=(
                f"adjustment:{user.pk}:{direction}:{normalized}:"
                f"{timezone.now().timestamp()}"
            ),
        )
        WalletUpdater.refresh(user)
        AuditLogger.record(
            actor=actor,
            action="ledger_adjustment",
            target_type="user",
            target_id=user.pk,
            new_value={
                "entry_id": entry.pk,
                "direction": direction,
                "amount_usd": str(normalized),
                "reason": reason.strip(),
            },
        )
        return entry

    @staticmethod
    @transaction.atomic
    def create_debt(
        user: User,
        *,
        amount_usd: Decimal | int | float | str,
        reason: str,
        actor: User,
    ) -> AdjustmentDebt:
        debt = AdjustmentService.create_debt(user, amount_usd, reason, actor)
        WalletUpdater.refresh(user)
        AuditLogger.record(
            actor=actor,
            action="adjustment_debt_created",
            target_type="adjustment_debt",
            target_id=debt.pk,
            new_value={
                "user_id": user.pk,
                "amount_usd": str(debt.amount_usd),
                "reason": reason,
            },
        )
        return debt
