from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.ledger.constants import (
    CURRENCY_USD,
    DIRECTION_CREDIT,
    DIRECTION_DEBIT,
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
            return Entry.objects.create(
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
        return model_name, source.pk


class AdjustmentService:
    """Скелет сервиса корректировок — полная логика в спринте 6."""

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
    def recover_from_credit(user: User, credit_amount: Decimal) -> Decimal:
        """Зарезервировано: удержание долга из следующих начислений."""
        return credit_amount
