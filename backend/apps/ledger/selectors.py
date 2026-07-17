from django.db.models import Sum

from apps.ledger.constants import DEBT_STATUS_OPEN
from apps.ledger.models import AdjustmentDebt, RuleVersion


def get_active_rule_version() -> RuleVersion | None:
    return RuleVersion.objects.order_by("-effective_from").first()


def get_open_adjustment_debt_usd(user_id: int):
    from django.db.models import Sum

    total = (
        AdjustmentDebt.objects.filter(
            user_id=user_id,
            status=DEBT_STATUS_OPEN,
        ).aggregate(total=Sum("remaining_usd"))["total"]
    )
    return total or 0
