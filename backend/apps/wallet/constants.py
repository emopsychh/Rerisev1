from decimal import Decimal

from apps.ledger.constants import (
    DEFAULT_WITHDRAWAL_CURRENCY,
    DEFAULT_WITHDRAWAL_MAX_PER_REQUEST_USD,
    DEFAULT_WITHDRAWAL_MIN_USD,
)

NETWORK_TRC20 = "TRC20"
NETWORK_ERC20 = "ERC20"

NETWORK_CHOICES = [
    (NETWORK_TRC20, "TRC20"),
    (NETWORK_ERC20, "ERC20"),
]

SUPPORTED_NETWORKS = {NETWORK_TRC20, NETWORK_ERC20}

WITHDRAWAL_STATUS_PENDING = "pending"
WITHDRAWAL_STATUS_APPROVED = "approved"
WITHDRAWAL_STATUS_PAID = "paid"
WITHDRAWAL_STATUS_REJECTED = "rejected"

WITHDRAWAL_STATUS_CHOICES = [
    (WITHDRAWAL_STATUS_PENDING, "Ожидает"),
    (WITHDRAWAL_STATUS_APPROVED, "Одобрен"),
    (WITHDRAWAL_STATUS_PAID, "Выплачен"),
    (WITHDRAWAL_STATUS_REJECTED, "Отклонён"),
]

PENDING_WITHDRAWAL_STATUSES = [
    WITHDRAWAL_STATUS_PENDING,
    WITHDRAWAL_STATUS_APPROVED,
]

TRANSACTION_FILTER_ALL = "all"
TRANSACTION_FILTER_BONUS = "bonus"
TRANSACTION_FILTER_WITHDRAWAL = "withdrawal"

TRANSACTION_FILTER_CHOICES = [
    TRANSACTION_FILTER_ALL,
    TRANSACTION_FILTER_BONUS,
    TRANSACTION_FILTER_WITHDRAWAL,
]

PERIOD_TODAY = "today"
PERIOD_YESTERDAY = "yesterday"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"

PERIOD_CHOICES = [
    PERIOD_TODAY,
    PERIOD_YESTERDAY,
    PERIOD_WEEK,
    PERIOD_MONTH,
]


def get_withdrawal_limits(rules: dict | None = None) -> dict:
    withdrawal = (rules or {}).get("withdrawal", {})
    return {
        "min_usd": Decimal(str(withdrawal.get("min_usd", DEFAULT_WITHDRAWAL_MIN_USD))),
        "max_per_request_usd": Decimal(
            str(withdrawal.get("max_per_request_usd", DEFAULT_WITHDRAWAL_MAX_PER_REQUEST_USD))
        ),
        "currency": withdrawal.get("currency", DEFAULT_WITHDRAWAL_CURRENCY),
    }
