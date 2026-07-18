from collections import deque
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.commerce.selectors import get_tariff_caps
from apps.ledger.constants import (
    CURRENCY_PV,
    CURRENCY_USD,
    ENTRY_TYPE_BINARY_BONUS,
    ENTRY_TYPE_BINARY_COLLAPSE,
    ENTRY_TYPE_FAST_START_BONUS,
    ENTRY_TYPE_MATCHING_BONUS,
    ENTRY_TYPE_PERSONAL_BONUS,
    ENTRY_TYPE_PURCHASE_PV,
    ENTRY_TYPE_RENEWAL_BONUS,
    ENTRY_TYPE_STATUS_PREMIUM,
    ENTRY_TYPE_SUBSCRIPTION_PV,
    ENTRY_TYPE_UPGRADE_PV,
)
from apps.ledger.services import LedgerWriter
from apps.partner.constants import LEG_LEFT, LEG_RIGHT
from apps.partner.engine_constants import (
    BINARY_PV_PER_USD,
    FAST_START_REQUIRED,
    FAST_START_REWARD,
    FAST_START_TARIFFS,
    FAST_START_WINDOW_DAYS,
    LEG_KEYS,
    MATCHING_RATE,
    MSK_TIMEZONE,
    RANKS,
    SUBSCRIPTION_PV,
    SUBSCRIPTION_SPONSOR_BONUS,
    rank_index,
)
from apps.partner.models import (
    BinaryBalance,
    BinaryPlacement,
    FastStart,
    PartnerProfile,
    QualificationWeek,
    RankHistory,
    SponsorLink,
)
from apps.partner.selectors import get_partner_profile, get_sponsor_partner
from apps.users.models import Notification
from apps.wallet.services import WalletUpdater


def calc_purchase_bonus(sponsor_tariff: str, buyer_tariff: str) -> tuple[Decimal, int]:
    """Начисление = min(тариф спонсора, тариф покупки)."""
    sponsor = get_tariff_caps(sponsor_tariff)
    buyer = get_tariff_caps(buyer_tariff)
    if not sponsor or not buyer:
        return Decimal("0"), 0
    return (
        min(Decimal(sponsor["bonus_usd"]), Decimal(buyer["bonus_usd"])),
        min(int(sponsor["pv"]), int(buyer["pv"])),
    )


class PersonalBonusService:
    @staticmethod
    def process(buyer: PartnerProfile, order) -> None:
        sponsor = get_sponsor_partner(buyer)
        if not sponsor or not sponsor.tariff_id:
            return

        bonus_usd, _pv = calc_purchase_bonus(sponsor.tariff_id, buyer.tariff_id)
        if bonus_usd <= 0:
            return

        # Денежный бонус — прямому спонсору (активному или неактивному <12 мес,
        # т.е. пока сохраняется tariff_id).
        LedgerWriter.credit(
            sponsor.user,
            ENTRY_TYPE_PERSONAL_BONUS,
            bonus_usd,
            CURRENCY_USD,
            source=order,
            idempotency_key=f"order:{order.id}:personal_bonus",
            metadata={"buyer_id": buyer.user_id, "buyer_tariff": buyer.tariff_id},
        )
        WalletUpdater.refresh(sponsor.user)
        _notify(
            sponsor.user,
            entry_type=ENTRY_TYPE_PERSONAL_BONUS,
            title="Личный бонус",
            body=f"Начислен личный бонус ${bonus_usd} за покупку приглашённого партнёра.",
            metadata={"order_id": order.id, "amount_usd": str(bonus_usd)},
        )


class PvDistributionService:
    @staticmethod
    def process(
        buyer: PartnerProfile,
        order,
        pv_amount: int,
        *,
        buyer_entry_type: str = ENTRY_TYPE_PURCHASE_PV,
    ) -> None:
        if pv_amount <= 0:
            return

        placement = BinaryPlacement.objects.filter(partner=buyer).first()
        if placement is None:
            return

        current = placement
        level = 0
        while current.parent_id is not None:
            level += 1
            parent = current.parent

            if parent.is_active:
                caps = get_tariff_caps(parent.tariff_id) if parent.tariff_id else None
                if caps and level <= caps["binary_depth"]:
                    _, pv_cap = calc_purchase_bonus(parent.tariff_id, buyer.tariff_id)
                    pv_for_parent = min(pv_amount, pv_cap)
                    if pv_for_parent > 0:
                        BinaryCollapseService.add_pv(
                            parent, current.leg, pv_for_parent, order
                        )

            next_placement = BinaryPlacement.objects.filter(partner=parent).first()
            if next_placement is None:
                break
            current = next_placement

        LedgerWriter.credit(
            buyer.user,
            buyer_entry_type,
            pv_amount,
            CURRENCY_PV,
            source=order,
            idempotency_key=f"order:{order.id}:{buyer_entry_type}:buyer",
        )


class BinaryCollapseService:
    @staticmethod
    def add_pv(partner: PartnerProfile, leg: str, amount: int, source) -> None:
        if not partner.is_active or amount <= 0:
            return

        balance, _ = BinaryBalance.objects.select_for_update().get_or_create(partner=partner)
        if balance.is_frozen:
            return

        if leg == LEG_LEFT:
            balance.left_pv += amount
        else:
            balance.right_pv += amount
        balance.save(update_fields=["left_pv", "right_pv", "updated_at"])

        BinaryCollapseService.collapse(partner, source)

    @staticmethod
    def collapse(partner: PartnerProfile, source) -> Decimal:
        if not partner.is_active:
            return Decimal("0")

        balance, _ = BinaryBalance.objects.select_for_update().get_or_create(partner=partner)
        if balance.is_frozen:
            return Decimal("0")

        collapsed = min(balance.left_pv, balance.right_pv)
        if collapsed == 0:
            return Decimal("0")

        balance.left_pv -= collapsed
        balance.right_pv -= collapsed
        balance.save(update_fields=["left_pv", "right_pv", "updated_at"])

        income_usd = (Decimal(collapsed) / Decimal(BINARY_PV_PER_USD)).quantize(Decimal("0.01"))

        source_id = getattr(source, "id", None) or getattr(source, "pk", None)
        collapse_key = (
            f"binary:{source_id}:{partner.user_id}:{collapsed}"
            if source_id is not None
            else None
        )

        LedgerWriter.credit(
            partner.user,
            ENTRY_TYPE_BINARY_COLLAPSE,
            collapsed,
            CURRENCY_PV,
            source=source,
            idempotency_key=f"{collapse_key}:pv" if collapse_key else None,
            metadata={"collapsed_pv": collapsed},
        )
        LedgerWriter.credit(
            partner.user,
            ENTRY_TYPE_BINARY_BONUS,
            income_usd,
            CURRENCY_USD,
            source=source,
            idempotency_key=f"{collapse_key}:usd" if collapse_key else None,
            metadata={"collapsed_pv": collapsed},
        )
        WalletUpdater.refresh(partner.user)

        QualificationWeekService.add_collapsed_pv(partner, collapsed)
        MatchingBonusService.process(partner, income_usd, source)
        StatusQualificationService.check(partner)
        return income_usd


class MatchingBonusService:
    @staticmethod
    def process(earner: PartnerProfile, binary_income_usd: Decimal, source) -> None:
        if binary_income_usd <= 0:
            return

        current_sponsor = get_sponsor_partner(earner)
        for line in range(1, 4):
            if not current_sponsor:
                break

            if not current_sponsor.is_active or not current_sponsor.tariff_id:
                current_sponsor = get_sponsor_partner(current_sponsor)
                continue

            caps = get_tariff_caps(current_sponsor.tariff_id)
            max_lines = caps["matching_lines"] if caps else 0
            if line > max_lines:
                # Тариф спонсора не покрывает эту линию — идём выше, не рвём цепочку.
                current_sponsor = get_sponsor_partner(current_sponsor)
                continue

            matching_usd = (binary_income_usd * MATCHING_RATE).quantize(Decimal("0.01"))
            if matching_usd > 0:
                source_id = getattr(source, "id", None) or getattr(source, "pk", None)
                LedgerWriter.credit(
                    current_sponsor.user,
                    ENTRY_TYPE_MATCHING_BONUS,
                    matching_usd,
                    CURRENCY_USD,
                    source=source,
                    idempotency_key=(
                        f"match:{source_id}:{earner.user_id}:{current_sponsor.user_id}:{line}"
                        if source_id is not None
                        else None
                    ),
                    metadata={
                        "from_partner": earner.user_id,
                        "line": line,
                        "binary_income": str(binary_income_usd),
                    },
                )
                WalletUpdater.refresh(current_sponsor.user)

            current_sponsor = get_sponsor_partner(current_sponsor)


class QualificationWeekService:
    @staticmethod
    def week_start(now=None):
        now = now or timezone.now()
        msk = now.astimezone(ZoneInfo(MSK_TIMEZONE))
        return msk.date() - timedelta(days=msk.weekday())

    @staticmethod
    def current(partner: PartnerProfile) -> QualificationWeek:
        week, _ = QualificationWeek.objects.get_or_create(
            partner=partner,
            week_start=QualificationWeekService.week_start(),
        )
        return week

    @staticmethod
    def add_collapsed_pv(partner: PartnerProfile, pv: int) -> QualificationWeek:
        week = QualificationWeekService.current(partner)
        QualificationWeek.objects.filter(pk=week.pk).update(
            collapsed_pv=F("collapsed_pv") + pv,
            updated_at=timezone.now(),
        )
        week.refresh_from_db(fields=["collapsed_pv"])
        return week


class StatusQualificationService:
    @staticmethod
    @transaction.atomic
    def check(partner: PartnerProfile) -> str | None:
        # Блокировка профиля сериализует параллельные проверки одного партнёра.
        partner = PartnerProfile.objects.select_for_update().get(pk=partner.pk)
        if not partner.is_active:
            return None

        week = QualificationWeekService.current(partner)
        collapsed_pv = week.collapsed_pv
        active_personals = count_active_direct_invites(partner)
        current_index = rank_index(partner.current_rank)

        achievable = []
        for rank_def in RANKS:
            if rank_index(rank_def["rank"]) <= current_index:
                continue
            if collapsed_pv < rank_def["pv"]:
                break
            if rank_def["personals"] and active_personals < rank_def["personals"]:
                continue
            if rank_def["leg_req"] and not has_qualifier_in_each_leg(
                partner, rank_def["leg_req"]
            ):
                continue
            achievable.append(rank_def)

        if not achievable:
            return None

        best = achievable[-1]
        partner.current_rank = best["rank"]
        partner.highest_rank = best["rank"]
        partner.save(update_fields=["current_rank", "highest_rank", "updated_at"])

        RankHistory.objects.create(
            partner=partner,
            rank=best["rank"],
            premium_usd=best["premium"],
            achieved_at=timezone.now(),
        )

        if best["premium"] > 0:
            LedgerWriter.credit(
                partner.user,
                ENTRY_TYPE_STATUS_PREMIUM,
                best["premium"],
                CURRENCY_USD,
                idempotency_key=f"status_premium:{partner.user_id}:{best['rank']}",
                metadata={"rank": best["rank"]},
            )
            WalletUpdater.refresh(partner.user)

        return best["rank"]


class FastStartService:
    @staticmethod
    def ensure_window(sponsor: PartnerProfile) -> FastStart | None:
        if sponsor.tariff_id not in FAST_START_TARIFFS:
            return None
        # Окно отсчитывается от первой покупки партнёрского тарифа спонсором
        # (placed_at выставляется при первом размещении в бинаре), а не от
        # первого приглашения. Апгрейд Rise → Pro окно не перезапускает.
        anchor = sponsor.placed_at or sponsor.created_at
        fs, _ = FastStart.objects.get_or_create(
            partner=sponsor,
            defaults={
                "window_start": anchor,
                "window_end": anchor + timedelta(days=FAST_START_WINDOW_DAYS),
            },
        )
        return fs

    @staticmethod
    def track_invite(sponsor: PartnerProfile, invited: PartnerProfile, order) -> None:
        if sponsor.tariff_id not in FAST_START_TARIFFS:
            return

        fs = FastStartService.ensure_window(sponsor)
        if fs is None or fs.reward_paid:
            return
        if timezone.now() > fs.window_end:
            return

        # Пересчёт: личные Pro/Max, размещённые в окне (включая Rise→Pro апгрейд).
        fs = FastStart.objects.select_for_update().get(pk=fs.pk)
        if fs.reward_paid:
            return

        count = SponsorLink.objects.filter(
            sponsor=sponsor,
            partner__tariff_id__in=FAST_START_TARIFFS,
            partner__placed_at__gte=fs.window_start,
            partner__placed_at__lte=fs.window_end,
        ).count()
        fs.qualified_count = count
        fs.save(update_fields=["qualified_count", "updated_at"])

        if fs.qualified_count >= FAST_START_REQUIRED:
            FastStartService._pay(sponsor, fs, order)

    @staticmethod
    def _pay(sponsor: PartnerProfile, fs: FastStart, order) -> None:
        LedgerWriter.credit(
            sponsor.user,
            ENTRY_TYPE_FAST_START_BONUS,
            FAST_START_REWARD,
            CURRENCY_USD,
            source=order,
            idempotency_key=f"fast_start:{fs.id}:paid",
        )
        WalletUpdater.refresh(sponsor.user)
        fs.reward_paid = True
        fs.reward_paid_at = timezone.now()
        fs.save(update_fields=["reward_paid", "reward_paid_at", "updated_at"])
        _notify(
            sponsor.user,
            entry_type=ENTRY_TYPE_FAST_START_BONUS,
            title="Быстрый старт выполнен",
            body=f"Поздравляем! Бонус быстрого старта ${FAST_START_REWARD} начислен.",
            metadata={"order_id": order.id},
        )


class BonusEngine:
    """Оркестратор: вызывает нужные сервисы по типу события заказа."""

    @staticmethod
    @transaction.atomic
    def process_purchase(order) -> None:
        buyer = get_partner_profile(order.user_id)
        if not buyer or not buyer.tariff_id:
            return

        caps = get_tariff_caps(buyer.tariff_id)
        pv_amount = caps["pv"] if caps else 0

        PersonalBonusService.process(buyer, order)
        PvDistributionService.process(buyer, order, pv_amount)
        StatusQualificationService.check(buyer)

        sponsor = get_sponsor_partner(buyer)
        if sponsor:
            FastStartService.track_invite(sponsor, buyer, order)

    @staticmethod
    @transaction.atomic
    def process_upgrade(order) -> None:
        buyer = get_partner_profile(order.user_id)
        if not buyer or not buyer.tariff_id:
            return

        old_tariff = order.previous_tariff_id
        new_tariff = buyer.tariff_id
        if not old_tariff or not get_tariff_caps(old_tariff) or not get_tariff_caps(new_tariff):
            return

        sponsor = get_sponsor_partner(buyer)
        # Дельта по матрице min(sponsor, tariff), а не «полный diff или ноль».
        if sponsor and sponsor.tariff_id:
            new_bonus, new_pv = calc_purchase_bonus(sponsor.tariff_id, new_tariff)
            old_bonus, old_pv = calc_purchase_bonus(sponsor.tariff_id, old_tariff)
            bonus_diff = new_bonus - old_bonus
            pv_diff = new_pv - old_pv

            if bonus_diff > 0:
                LedgerWriter.credit(
                    sponsor.user,
                    ENTRY_TYPE_PERSONAL_BONUS,
                    bonus_diff,
                    CURRENCY_USD,
                    source=order,
                    idempotency_key=f"order:{order.id}:upgrade_bonus",
                    metadata={
                        "buyer_id": buyer.user_id,
                        "upgrade": f"{old_tariff}->{new_tariff}",
                    },
                )
                WalletUpdater.refresh(sponsor.user)
        else:
            # Без спонсора денежный бонус некому; PV всё равно идёт вверх по бинару.
            old_caps = get_tariff_caps(old_tariff)
            new_caps = get_tariff_caps(new_tariff)
            pv_diff = int(new_caps["pv"]) - int(old_caps["pv"])

        if pv_diff > 0:
            PvDistributionService.process(
                buyer, order, pv_diff, buyer_entry_type=ENTRY_TYPE_UPGRADE_PV
            )

        # Fast Start: Rise→Pro/Max в окне должен засчитаться.
        if sponsor:
            FastStartService.track_invite(sponsor, buyer, order)

    @staticmethod
    @transaction.atomic
    def process_renewal(order) -> None:
        buyer = get_partner_profile(order.user_id)
        if not buyer:
            return

        sponsor = get_sponsor_partner(buyer)
        if sponsor and sponsor.is_active and sponsor.tariff_id:
            LedgerWriter.credit(
                sponsor.user,
                ENTRY_TYPE_RENEWAL_BONUS,
                SUBSCRIPTION_SPONSOR_BONUS,
                CURRENCY_USD,
                source=order,
                idempotency_key=f"order:{order.id}:renewal_bonus",
                metadata={"buyer_id": buyer.user_id},
            )
            WalletUpdater.refresh(sponsor.user)

        PvDistributionService.process(
            buyer, order, SUBSCRIPTION_PV, buyer_entry_type=ENTRY_TYPE_SUBSCRIPTION_PV
        )


# --- Вспомогательные функции чтения дерева ---


def count_active_direct_invites(partner: PartnerProfile) -> int:
    return SponsorLink.objects.filter(sponsor=partner, partner__is_active=True).count()


def _leg_root(partner: PartnerProfile, leg: str) -> PartnerProfile | None:
    placement = (
        BinaryPlacement.objects.filter(parent=partner, leg=leg)
        .select_related("partner")
        .first()
    )
    return placement.partner if placement else None


def _iter_subtree(root: PartnerProfile):
    queue = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        children = BinaryPlacement.objects.filter(parent=node).select_related("partner")
        for child in children:
            queue.append(child.partner)


def has_qualifier_in_each_leg(partner: PartnerProfile, required_rank: str) -> bool:
    required_index = rank_index(required_rank)
    for leg in LEG_KEYS:
        root = _leg_root(partner, leg)
        if root is None:
            return False
        if not _leg_has_qualifier(root, required_index):
            return False
    return True


def _leg_has_qualifier(root: PartnerProfile, required_index: int) -> bool:
    for node in _iter_subtree(root):
        if node.is_active and rank_index(node.highest_rank) >= required_index:
            return True
    return False


def _notify(user, *, entry_type: str, title: str, body: str, metadata: dict) -> None:
    Notification.objects.create(
        user=user,
        type="bonus",
        title=title,
        body=body,
        metadata={**metadata, "entry_type": entry_type},
    )
