from datetime import timedelta

from django.utils import timezone

from apps.ledger.constants import (
    BONUS_ENTRY_TYPES,
    CURRENCY_USD,
    ENTRY_TYPE_TITLES,
    ENTRY_TYPE_WITHDRAWAL,
)
from apps.ledger.models import Entry
from apps.ledger.selectors import get_active_rule_version, get_open_adjustment_debt_usd
from apps.wallet.constants import (
    PERIOD_CHOICES,
    PERIOD_MONTH,
    PERIOD_TODAY,
    PERIOD_WEEK,
    PERIOD_YESTERDAY,
    TRANSACTION_FILTER_ALL,
    TRANSACTION_FILTER_BONUS,
    TRANSACTION_FILTER_WITHDRAWAL,
    get_withdrawal_limits,
)
from apps.wallet.models import Balance, SavedAddress
from apps.wallet.services import WalletUpdater


def get_active_withdrawal_limits() -> dict:
    rule_version = get_active_rule_version()
    return get_withdrawal_limits(rule_version.rules if rule_version else None)


def get_default_saved_address(user) -> SavedAddress | None:
    return SavedAddress.objects.filter(user=user, is_default=True).first()


def serialize_transaction(entry: Entry) -> dict:
    return {
        "id": entry.id,
        "entry_type": entry.entry_type,
        "type": entry.entry_type,
        "title": ENTRY_TYPE_TITLES.get(entry.entry_type, entry.entry_type),
        "amount_usd": float(entry.amount),
        "direction": entry.direction,
        "created_at": entry.created_at.isoformat().replace("+00:00", "Z"),
    }


def serialize_recent_transaction(entry: Entry) -> dict:
    payload = serialize_transaction(entry)
    return {key: payload[key] for key in ("id", "type", "title", "amount_usd", "direction", "created_at")}


def get_wallet_overview(user) -> dict:
    balance = WalletUpdater.refresh(user)
    limits = get_active_withdrawal_limits()
    saved = get_default_saved_address(user)

    recent = (
        Entry.objects.filter(user=user, currency=CURRENCY_USD)
        .order_by("-created_at")[:5]
    )

    return {
        "balance": {
            "available_usd": float(balance.available_usd),
            "pending_usd": float(balance.pending_usd),
            "total_earned_usd": float(balance.total_earned_usd),
        },
        "adjustment_debt_usd": float(get_open_adjustment_debt_usd(user.pk)),
        "withdrawal_limits": {
            "min_usd": float(limits["min_usd"]),
            "max_per_request_usd": float(limits["max_per_request_usd"]),
            "currency": limits["currency"],
        },
        "saved_address": (
            {"address": saved.address, "network": saved.network}
            if saved
            else None
        ),
        "recent_transactions": [
            serialize_recent_transaction(entry) for entry in recent
        ],
    }


def get_transaction_queryset(user, *, entry_type: str, period: str | None):
    queryset = Entry.objects.filter(user=user, currency=CURRENCY_USD)

    if entry_type == TRANSACTION_FILTER_BONUS:
        queryset = queryset.filter(entry_type__in=BONUS_ENTRY_TYPES)
    elif entry_type == TRANSACTION_FILTER_WITHDRAWAL:
        queryset = queryset.filter(entry_type=ENTRY_TYPE_WITHDRAWAL)

    if period and period in PERIOD_CHOICES:
        now = timezone.now()
        if period == PERIOD_TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == PERIOD_YESTERDAY:
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = today_start - timedelta(days=1)
            now = today_start
        elif period == PERIOD_WEEK:
            start = now - timedelta(days=7)
        elif period == PERIOD_MONTH:
            start = now - timedelta(days=30)
        else:
            start = None

        if start is not None:
            queryset = queryset.filter(created_at__gte=start, created_at__lt=now)

    return queryset.order_by("-created_at")


def serialize_withdrawal_request(request) -> dict:
    return {
        "id": request.id,
        "amount_usd": float(request.amount_usd),
        "fee_usd": float(request.fee_usd),
        "status": request.status,
        "created_at": request.created_at.isoformat().replace("+00:00", "Z"),
    }


def serialize_saved_address(saved: SavedAddress) -> dict:
    return {
        "address": saved.address,
        "network": saved.network,
    }
