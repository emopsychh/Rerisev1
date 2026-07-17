from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.ibox.constants import REASON_GENERATION, REASON_REFUND
from apps.ibox.models import ChatSession, TokenBalance, TokenTransaction
from apps.users.models import User


class InsufficientTokensError(Exception):
    def __init__(self, available: int, required: int):
        self.available = available
        self.required = required
        super().__init__(f"Недостаточно токенов: нужно {required}, доступно {available}")


class TokenService:
    @staticmethod
    def get_or_create_balance(user: User) -> TokenBalance:
        balance, _ = TokenBalance.objects.get_or_create(user=user)
        return balance

    @staticmethod
    def get_available(user: User) -> int:
        balance = TokenBalance.objects.filter(user=user).first()
        return balance.available if balance else 0

    @staticmethod
    def _locked_balance(user: User) -> TokenBalance:
        """get_or_create + select_for_update без гонки на первом create."""
        try:
            balance, _ = TokenBalance.objects.get_or_create(user=user)
        except IntegrityError:
            balance = TokenBalance.objects.get(user=user)

        return TokenBalance.objects.select_for_update().get(pk=balance.pk)

    @staticmethod
    @transaction.atomic
    def credit(
        user: User,
        amount: int,
        *,
        reason: str,
        order=None,
        session: ChatSession | None = None,
    ) -> TokenBalance:
        if amount <= 0:
            raise ValueError("amount must be positive")

        balance = TokenService._locked_balance(user)
        balance.available += amount
        balance.save(update_fields=["available", "updated_at"])

        TokenTransaction.objects.create(
            user=user,
            amount=amount,
            reason=reason,
            order=order,
            session=session,
        )
        return balance

    @staticmethod
    @transaction.atomic
    def debit(
        user: User,
        amount: int,
        *,
        reason: str = REASON_GENERATION,
        session: ChatSession | None = None,
        order=None,
    ) -> TokenBalance:
        if amount <= 0:
            raise ValueError("amount must be positive")

        balance = TokenService._locked_balance(user)
        if balance.available < amount:
            raise InsufficientTokensError(balance.available, amount)

        balance.available -= amount
        balance.used_this_month += amount
        if balance.month_reset_at is None:
            balance.month_reset_at = timezone.now()
        balance.save(
            update_fields=["available", "used_this_month", "month_reset_at", "updated_at"]
        )

        TokenTransaction.objects.create(
            user=user,
            amount=-amount,
            reason=reason,
            order=order,
            session=session,
        )
        return balance

    @staticmethod
    def refund(
        user: User,
        amount: int,
        *,
        session: ChatSession | None = None,
    ) -> TokenBalance:
        return TokenService.credit(
            user,
            amount,
            reason=REASON_REFUND,
            session=session,
        )
