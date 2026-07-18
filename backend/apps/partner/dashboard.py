from datetime import timedelta

from apps.commerce.selectors import get_tariff_caps, get_tariff_display_name
from apps.ledger.constants import CURRENCY_USD, ENTRY_TYPE_TITLES
from apps.ledger.models import Entry
from apps.partner.constants import LEG_LEFT, LEG_RIGHT
from apps.partner.engine import count_active_direct_invites
from apps.partner.engine_constants import (
    FAST_START_REQUIRED,
    FAST_START_REWARD,
    RANK_BY_ID,
    RANKS,
    next_rank_id,
    rank_index,
    rank_name,
    rank_requirement_text,
)
from apps.partner.models import (
    BinaryBalance,
    BinaryPlacement,
    FastStart,
    PartnerProfile,
    RankHistory,
)
from apps.partner.selectors import format_partner_name, get_personal_invites
from apps.wallet.services import WalletUpdater

RU_MONTHS = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

LEG_TITLES = {LEG_LEFT: "Левая ветка", LEG_RIGHT: "Правая ветка"}


def _leg_children(partner: PartnerProfile, leg: str):
    return (
        BinaryPlacement.objects.filter(parent=partner, leg=leg)
        .select_related("partner__user__profile")
        .first()
    )


def _collect_levels(partner: PartnerProfile, max_depth: int) -> list[dict]:
    """BFS по бинарному поддереву: агрегаты по относительным уровням L1..max_depth."""
    levels: dict[int, dict] = {}
    frontier = [
        placement.partner
        for placement in BinaryPlacement.objects.filter(parent=partner).select_related("partner")
    ]

    level = 1
    while frontier and level <= max_depth:
        balances = {
            balance.partner_id: balance
            for balance in BinaryBalance.objects.filter(partner__in=frontier)
        }
        bucket = {"level": f"L{level}", "total": 0, "active": 0, "pv": 0}
        next_frontier = []
        for node in frontier:
            bucket["total"] += 1
            if node.is_active:
                bucket["active"] += 1
            balance = balances.get(node.pk)
            if balance:
                bucket["pv"] += balance.left_pv + balance.right_pv
            next_frontier.extend(
                placement.partner
                for placement in BinaryPlacement.objects.filter(parent=node).select_related(
                    "partner"
                )
            )
        levels[level] = bucket
        frontier = next_frontier
        level += 1

    return [levels[key] for key in sorted(levels)]


def _format_period(week_start) -> str:
    week_end = week_start + timedelta(days=6)
    if week_start.month == week_end.month:
        return f"{week_start.day}–{week_end.day} {RU_MONTHS[week_end.month]} · МСК"
    return (
        f"{week_start.day} {RU_MONTHS[week_start.month]} – "
        f"{week_end.day} {RU_MONTHS[week_end.month]} · МСК"
    )


def _current_week(partner: PartnerProfile):
    from apps.partner.engine import QualificationWeekService

    return QualificationWeekService.current(partner)


def build_dashboard(user) -> dict:
    from apps.partner.selectors import get_partner_profile

    partner = get_partner_profile(user.pk)
    if not partner or not partner.tariff_id:
        return {"is_partner": False}

    balance = WalletUpdater.refresh(user)
    caps = get_tariff_caps(partner.tariff_id) or {}
    depth_limit = caps.get("binary_depth", 0)

    week = _current_week(partner)
    active_personals = count_active_direct_invites(partner)
    next_rank = next_rank_id(partner.current_rank)
    next_rank_def = RANK_BY_ID.get(next_rank) if next_rank else None

    fast_start = FastStart.objects.filter(partner=partner).first()

    recent_entries = (
        Entry.objects.filter(user=user, currency=CURRENCY_USD)
        .order_by("-created_at")[:10]
    )

    index = rank_index(partner.current_rank)
    member_label = f"RE:RISE MEMBER {index + 1:02d} / {len(RANKS)}"

    metrics = {
        "weekly_collapsed_pv": {
            "current": week.collapsed_pv,
            "required": next_rank_def["pv"] if next_rank_def else None,
            "next_rank": rank_name(next_rank) if next_rank else None,
        },
        "active_personal_partners": {
            "current": active_personals,
            "required": next_rank_def["personals"] if next_rank_def else None,
            "next_rank": rank_name(next_rank) if next_rank else None,
        },
        "fast_start": {
            "current": fast_start.qualified_count if fast_start else 0,
            "required": FAST_START_REQUIRED,
            "reward_usd": float(FAST_START_REWARD),
            "reward_paid": fast_start.reward_paid if fast_start else False,
        },
        "available_to_withdraw": {"amount_usd": float(balance.available_usd)},
    }

    qualification_week = {
        "title": f"Движение к «{rank_name(next_rank)}»" if next_rank else "Максимальный статус",
        "period": _format_period(week.week_start),
        "week_start": week.week_start.isoformat(),
        "week_end": (week.week_start + timedelta(days=6)).isoformat(),
        "rows": [
            {
                "label": "Схлоп за неделю",
                "current": week.collapsed_pv,
                "required": next_rank_def["pv"] if next_rank_def else None,
                "unit": "PV",
            },
            {
                "label": "Активные личные",
                "current": active_personals,
                "required": next_rank_def["personals"] if next_rank_def else None,
            },
            {
                "label": "Бинарный доход",
                "current": round(week.collapsed_pv / 10, 2),
                "unit": "USD",
                "formula": "10 PV = $1",
            },
        ],
    }

    return {
        "is_partner": True,
        "member_label": member_label,
        "balance": {
            "total_usd": float(balance.total_earned_usd),
            "available_usd": float(balance.available_usd),
        },
        "partner": {
            "tariff_id": partner.tariff_id,
            "tariff_name": get_tariff_display_name(partner.tariff_id),
            "is_active": partner.is_active,
            "activity_until": partner.activity_until,
            "current_rank": partner.current_rank,
            "current_rank_name": rank_name(partner.current_rank),
            "next_rank": next_rank,
            "next_rank_name": rank_name(next_rank) if next_rank else None,
        },
        "team_depth": {
            "tariff_depth_limit": depth_limit,
            "levels": _collect_levels(partner, depth_limit),
        },
        "metrics": metrics,
        "qualification_week": qualification_week,
        "updates": [_serialize_update(entry) for entry in recent_entries],
        "can_renew": _can_renew(partner),
    }


def _can_renew(partner: PartnerProfile) -> bool:
    from apps.commerce.selectors import get_user_subscription, subscription_can_renew

    return subscription_can_renew(get_user_subscription(partner.user_id))


def _serialize_update(entry: Entry) -> dict:
    return {
        "id": entry.id,
        "type": entry.entry_type,
        "title": ENTRY_TYPE_TITLES.get(entry.entry_type, entry.entry_type),
        "amount_usd": float(entry.amount),
        "created_at": entry.created_at.isoformat().replace("+00:00", "Z"),
    }


def _achieved_at_by_rank(partner: PartnerProfile) -> dict:
    achieved: dict = {}
    for entry in (
        RankHistory.objects.filter(partner=partner).order_by("achieved_at")
    ):
        achieved.setdefault(entry.rank, entry.achieved_at)
    return achieved


def build_ranks(partner: PartnerProfile) -> list[dict]:
    week = _current_week(partner)
    active_personals = count_active_direct_invites(partner)
    achieved_index = rank_index(partner.highest_rank)

    achieved_at_by_rank = _achieved_at_by_rank(partner)

    result = []
    for rank_def in RANKS:
        is_achieved = rank_index(rank_def["rank"]) <= achieved_index
        row = {
            "rank": rank_def["rank"],
            "name": rank_name(rank_def["rank"]),
            "weekly_collapsed_pv": rank_def["pv"],
            "requirement": rank_requirement_text(rank_def),
            "reward_usd": float(rank_def["premium"]),
            "is_achieved": is_achieved,
        }
        if is_achieved:
            # Стартовый partner_1 выдаётся при покупке без записи в RankHistory —
            # берём дату размещения в бинаре как момент достижения.
            achieved_at = achieved_at_by_rank.get(rank_def["rank"]) or partner.placed_at
            row["achieved_at"] = (
                achieved_at.isoformat().replace("+00:00", "Z") if achieved_at else None
            )
        if not is_achieved:
            row["progress"] = {
                "collapsed_pv": {"current": week.collapsed_pv, "required": rank_def["pv"]},
                "active_personals": {
                    "current": active_personals,
                    "required": rank_def["personals"],
                },
            }
        result.append(row)
    return result


def _leg_summary(partner: PartnerProfile, leg: str, max_depth: int) -> dict:
    root_placement = _leg_children(partner, leg)
    members = 0
    active = 0
    total_pv = 0
    recent = []
    lead = None

    if root_placement:
        lead = format_partner_name(root_placement.partner.user.profile)
        frontier = [root_placement.partner]
        level = 1
        while frontier and level <= max_depth:
            balances = {
                balance.partner_id: balance
                for balance in BinaryBalance.objects.filter(partner__in=frontier)
            }
            next_frontier = []
            for node in frontier:
                members += 1
                if node.is_active:
                    active += 1
                balance = balances.get(node.pk)
                if balance:
                    total_pv += balance.left_pv + balance.right_pv
                if len(recent) < 3:
                    recent.append(format_partner_name(node.user.profile))
                next_frontier.extend(
                    placement.partner
                    for placement in BinaryPlacement.objects.filter(parent=node).select_related(
                        "partner__user__profile"
                    )
                )
            frontier = next_frontier
            level += 1

    return {
        "id": leg,
        "title": LEG_TITLES[leg],
        "lead": lead,
        "pv": total_pv,
        "members": members,
        "active": active,
        "recent": recent,
    }


def build_structure(partner: PartnerProfile, *, leg: str | None = None, depth: int = 3) -> dict:
    legs_to_show = [leg] if leg in (LEG_LEFT, LEG_RIGHT) else [LEG_LEFT, LEG_RIGHT]
    legs = [_leg_summary(partner, item, depth) for item in legs_to_show]

    total_members = sum(item["members"] for item in legs)
    active_members = sum(item["active"] for item in legs)
    total_pv = sum(item["pv"] for item in legs)
    personal_invites = get_personal_invites(partner).count()

    members = []
    for item in legs:
        placement = _leg_children(partner, item["id"])
        if not placement:
            continue
        for entry in _iter_leg_members(placement.partner, item["id"], depth):
            members.append(entry)

    return {
        "legs": legs,
        "summary": {
            "total_members": total_members,
            "active_members": active_members,
            "personal_invites": personal_invites,
            "total_pv": total_pv,
        },
        "members": members,
        "tree": {
            "root_id": "self",
            "directory": _build_tree_directory(partner, depth),
        },
    }


def _iter_leg_members(root: PartnerProfile, leg: str, max_depth: int):
    frontier = [root]
    level = 1
    while frontier and level <= max_depth:
        balances = {
            balance.partner_id: balance
            for balance in BinaryBalance.objects.filter(partner__in=frontier)
        }
        next_frontier = []
        for node in frontier:
            balance = balances.get(node.pk)
            pv = (balance.left_pv + balance.right_pv) if balance else 0
            activity = (
                f"Активен до {node.activity_until:%d.%m.%Y}"
                if node.is_active and node.activity_until
                else "Неактивен"
            )
            yield {
                "id": str(node.pk),
                "name": format_partner_name(node.user.profile),
                "branch": LEG_TITLES[leg],
                "branch_id": leg,
                "level": f"L{level}",
                "pv": pv,
                "status": "Активен" if node.is_active else "Неактивен",
                "activity": activity,
                "active": node.is_active,
            }
            next_frontier.extend(
                placement.partner
                for placement in BinaryPlacement.objects.filter(parent=node).select_related(
                    "partner__user__profile"
                )
            )
        frontier = next_frontier
        level += 1


def _subtree_counts(partner: PartnerProfile, max_depth: int) -> tuple[int, int]:
    """Число партнёров в поддереве (включая корень) и сколько из них активны."""
    total = 1
    active = 1 if partner.is_active else 0
    if max_depth <= 0:
        return total, active
    frontier = [
        placement.partner
        for placement in BinaryPlacement.objects.filter(parent=partner).select_related("partner")
    ]
    depth = 1
    while frontier and depth <= max_depth:
        next_frontier = []
        for node in frontier:
            total += 1
            if node.is_active:
                active += 1
            next_frontier.extend(
                placement.partner
                for placement in BinaryPlacement.objects.filter(parent=node).select_related("partner")
            )
        frontier = next_frontier
        depth += 1
    return total, active


def _build_tree_directory(partner: PartnerProfile, max_depth: int) -> dict:
    """Словарь узлов бинара: корень = self, дети = left/right ids."""
    directory: dict = {}
    partner = PartnerProfile.objects.select_related("user__profile").get(pk=partner.pk)

    def visit(
        node: PartnerProfile,
        *,
        node_id: str,
        parent_id: str | None,
        branch_id: str | None,
        level: int,
        remaining_depth: int,
    ) -> None:
        left_placement = _leg_children(node, LEG_LEFT) if remaining_depth > 0 else None
        right_placement = _leg_children(node, LEG_RIGHT) if remaining_depth > 0 else None
        left_id = str(left_placement.partner_id) if left_placement else None
        right_id = str(right_placement.partner_id) if right_placement else None

        if left_placement and remaining_depth > 0:
            visit(
                left_placement.partner,
                node_id=left_id,  # type: ignore[arg-type]
                parent_id=node_id,
                branch_id=LEG_LEFT,
                level=level + 1,
                remaining_depth=remaining_depth - 1,
            )
        if right_placement and remaining_depth > 0:
            visit(
                right_placement.partner,
                node_id=right_id,  # type: ignore[arg-type]
                parent_id=node_id,
                branch_id=LEG_RIGHT,
                level=level + 1,
                remaining_depth=remaining_depth - 1,
            )

        name = format_partner_name(node.user.profile)
        initial = (name[:1] or "R").upper()
        team_size, active_team = _subtree_counts(node, remaining_depth)
        balance = BinaryBalance.objects.filter(partner=node).first()
        pv = (balance.left_pv + balance.right_pv) if balance else 0

        directory[node_id] = {
            "id": node_id,
            "name": name,
            "initial": initial,
            "rank": rank_name(node.current_rank),
            "parentId": parent_id,
            "branchId": branch_id,
            "level": f"L{level}",
            "active": node.is_active,
            "children": [left_id, right_id],
            "teamSize": team_size,
            "activeTeam": active_team,
            "remainingPv": pv,
            "pv": pv,
        }

    visit(
        partner,
        node_id="self",
        parent_id=None,
        branch_id=None,
        level=0,
        remaining_depth=max_depth,
    )
    return directory
