from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.ledger.constants import (
    CURRENCY_USD,
    DEBT_STATUS_OPEN,
    DEBT_STATUS_PAID,
    DIRECTION_CREDIT,
    DIRECTION_DEBIT,
    ENTRY_TYPE_ADJUSTMENT,
    SOURCE_TYPE_ADMIN,
    SOURCE_TYPE_ORDER,
    SOURCE_TYPE_PARTNER,
    SOURCE_TYPE_WITHDRAWAL,
)
from apps.ledger.models import AdjustmentDebt, Entry
from apps.ledger.selectors import get_active_rule_version
from apps.users.models import User


class LedgerError(ValueError):
    pass


class LedgerWriter:
    @staticmethod
    def credit(
        user: User,
        entry_type: str,
        amount: Decimal | int | float | str,
        currency: str = CURRENCY_USD,
        *,
        source=None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
        description: str | None = None,
    ) -> Entry:
        return LedgerWriter._write(
            user=user,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            direction=DIRECTION_CREDIT,
            source=source,
            metadata=metadata,
            idempotency_key=idempotency_key,
            description=description,
        )

    @staticmethod
    def debit(
        user: User,
        entry_type: str,
        amount: Decimal | int | float | str,
        currency: str = CURRENCY_USD,
        *,
        source=None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
        description: str | None = None,
    ) -> Entry:
        return LedgerWriter._write(
            user=user,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            direction=DIRECTION_DEBIT,
            source=source,
            metadata=metadata,
            idempotency_key=idempotency_key,
            description=description,
        )

    @staticmethod
    @transaction.atomic
    def _write(
        *,
        user: User,
        entry_type: str,
        amount: Decimal | int | float | str,
        currency: str,
        direction: str,
        source=None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
        description: str | None = None,
    ) -> Entry:
        normalized_amount = Decimal(str(amount))
        if normalized_amount <= 0:
            raise LedgerError("Сумма записи должна быть больше нуля")

        if idempotency_key:
            existing = Entry.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                LedgerWriter._assert_idempotent_match(
                    existing,
                    user=user,
                    entry_type=entry_type,
                    amount=normalized_amount,
                    currency=currency,
                    direction=direction,
                )
                return existing

        rule_version = get_active_rule_version()
        if not rule_version:
            raise LedgerError("Нет активной версии правил ledger. Запустите seed_ledger_rules.")

        source_type, source_id = LedgerWriter._resolve_source(source)

        try:
            entry = Entry.objects.create(
                user=user,
                entry_type=entry_type,
                amount=normalized_amount,
                currency=currency,
                direction=direction,
                source_type=source_type,
                source_id=source_id,
                rule_version=rule_version,
                description=description,
                metadata=metadata or {},
                idempotency_key=idempotency_key,
            )
        except IntegrityError:
            if not idempotency_key:
                raise
            existing = Entry.objects.get(idempotency_key=idempotency_key)
            LedgerWriter._assert_idempotent_match(
                existing,
                user=user,
                entry_type=entry_type,
                amount=normalized_amount,
                currency=currency,
                direction=direction,
            )
            return existing

        if (
            currency == CURRENCY_USD
            and direction == DIRECTION_CREDIT
            and entry_type != ENTRY_TYPE_ADJUSTMENT
        ):
            AdjustmentService.recover_from_credit(user, normalized_amount)

        return entry

    @staticmethod
    def _assert_idempotent_match(
        existing: Entry,
        *,
        user: User,
        entry_type: str,
        amount: Decimal,
        currency: str,
        direction: str,
    ) -> None:
        if (
            existing.user_id != user.pk
            or existing.entry_type != entry_type
            or existing.amount != amount
            or existing.currency != currency
            or existing.direction != direction
        ):
            raise LedgerError(
                f"Idempotency key уже использован с другими параметрами: {existing.idempotency_key}"
            )

    @staticmethod
    def _resolve_source(source) -> tuple[str | None, int | None]:
        if source is None:
            return None, None

        model_name = source._meta.model_name
        if model_name == "order":
            return SOURCE_TYPE_ORDER, source.pk
        if model_name in ("partnerprofile", "sponsorlink"):
            return SOURCE_TYPE_PARTNER, source.pk
        if model_name == "withdrawalrequest":
            return SOURCE_TYPE_WITHDRAWAL, source.pk
        if model_name == "user":
            return SOURCE_TYPE_ADMIN, source.pk
        if model_name == "adjustmentdebt":
            return SOURCE_TYPE_ADMIN, source.pk
        return model_name, source.pk


class AdjustmentService:
    """Корректировочные долги и удержание из следующих USD-начислений."""

    @staticmethod
    @transaction.atomic
    def create_debt(
        user: User,
        amount_usd: Decimal | int | float | str,
        reason: str,
        created_by: User,
    ) -> AdjustmentDebt:
        normalized = Decimal(str(amount_usd))
        if normalized <= 0:
            raise LedgerError("Сумма долга должна быть больше нуля")

        return AdjustmentDebt.objects.create(
            user=user,
            amount_usd=normalized,
            remaining_usd=normalized,
            reason=reason,
            created_by=created_by,
        )

    @staticmethod
    @transaction.atomic
    def recover_from_credit(user: User, credit_amount: Decimal) -> Decimal:
        """Списывает открытые долги из нового USD-кредита. Возвращает остаток кредита."""
        remaining_credit = Decimal(str(credit_amount))
        if remaining_credit <= 0:
            return Decimal("0")

        debts = (
            AdjustmentDebt.objects.select_for_update()
            .filter(user=user, status=DEBT_STATUS_OPEN, remaining_usd__gt=0)
            .order_by("created_at", "id")
        )
        for debt in debts:
            if remaining_credit <= 0:
                break
            take = min(debt.remaining_usd, remaining_credit)
            if take <= 0:
                continue

            already_recovered = debt.amount_usd - debt.remaining_usd
            LedgerWriter.debit(
                user=user,
                entry_type=ENTRY_TYPE_ADJUSTMENT,
                amount=take,
                currency=CURRENCY_USD,
                source=debt,
                description=f"Погашение долга #{debt.pk}",
                metadata={"debt_id": debt.pk, "reason": debt.reason},
                idempotency_key=f"debt:{debt.pk}:recovered:{already_recovered + take}",
            )
            debt.remaining_usd -= take
            remaining_credit -= take
            update_fields = ["remaining_usd"]
            if debt.remaining_usd <= 0:
                debt.remaining_usd = Decimal("0")
                debt.status = DEBT_STATUS_PAID
                debt.resolved_at = timezone.now()
                update_fields.extend(["status", "resolved_at"])
            debt.save(update_fields=update_fields)

        return remaining_credit
