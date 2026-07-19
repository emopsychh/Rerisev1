from collections import deque

from django.db import transaction
from django.utils import timezone

from apps.commerce.selectors import get_user_subscription
from apps.partner.constants import (
    DEFAULT_RANK,
    FIRST_PERSONAL_INVITE_COUNT,
    LEG_LEFT,
    LEG_RIGHT,
)
from apps.partner.models import BinaryBalance, BinaryPlacement, PartnerProfile, SponsorLink
from apps.partner.selectors import get_sponsor_partner
from apps.users.models import User


class BinaryPlacementError(ValueError):
    pass


class ActivityService:
    @staticmethod
    def sync_from_subscription(partner: PartnerProfile) -> PartnerProfile:
        subscription = get_user_subscription(partner.user_id)
        if not subscription:
            partner.is_active = False
            partner.save(update_fields=["is_active", "updated_at"])
            return partner

        partner.tariff_id = subscription.tariff_id
        partner.activity_until = subscription.active_until
        partner.is_active = subscription.is_active
        partner.save(
            update_fields=[
                "tariff_id",
                "activity_until",
                "is_active",
                "updated_at",
            ]
        )
        return partner

    @staticmethod
    def set_frozen(partner: PartnerProfile, *, frozen: bool) -> None:
        balance, _ = BinaryBalance.objects.get_or_create(partner=partner)
        if balance.is_frozen != frozen:
            balance.is_frozen = frozen
            balance.save(update_fields=["is_frozen", "updated_at"])

    @staticmethod
    def expire_due() -> int:
        """Истёкшая активность → is_active=False, бинар заморожен.
        После ~12 мес. непрерывной неактивности — сброс tariff_id (маркетинг §10).
        """
        from datetime import timedelta

        from apps.partner.engine_constants import INACTIVITY_TARIFF_LOSS_MONTHS

        now = timezone.now()
        due = PartnerProfile.objects.filter(is_active=True, activity_until__lt=now)
        count = 0
        for partner in due:
            partner.is_active = False
            partner.save(update_fields=["is_active", "updated_at"])
            ActivityService.set_frozen(partner, frozen=True)
            count += 1

        # ~30.44 дня × N месяцев
        loss_before = now - timedelta(days=int(INACTIVITY_TARIFF_LOSS_MONTHS * 30.44))
        lost = PartnerProfile.objects.filter(
            is_active=False,
            tariff_id__isnull=False,
            activity_until__lt=loss_before,
            tariff_lost_at__isnull=True,
        )
        for partner in lost:
            partner.tariff_id = None
            partner.tariff_lost_at = now
            partner.save(update_fields=["tariff_id", "tariff_lost_at", "updated_at"])
            balance, _ = BinaryBalance.objects.get_or_create(partner=partner)
            if balance.left_pv or balance.right_pv:
                balance.left_pv = 0
                balance.right_pv = 0
                balance.save(update_fields=["left_pv", "right_pv", "updated_at"])

        return count


class BinaryPlacementService:
    @staticmethod
    def place_if_needed(partner: PartnerProfile, leg: str | None = None) -> BinaryPlacement:
        existing = BinaryPlacement.objects.filter(partner=partner).first()
        if existing:
            return existing

        sponsor = get_sponsor_partner(partner)
        if sponsor is None:
            return BinaryPlacementService._place_as_root(partner)

        if not BinaryPlacement.objects.filter(partner=sponsor).exists():
            raise BinaryPlacementError("Спонсор ещё не размещён в бинаре")

        resolved_leg = BinaryPlacementService._resolve_leg(sponsor, leg)
        parent, slot_leg, depth = BinaryPlacementService._find_first_free_slot(
            sponsor, resolved_leg
        )
        return BinaryPlacementService._create_placement(
            partner, parent=parent, leg=slot_leg, depth=depth
        )

    @staticmethod
    def _resolve_leg(sponsor: PartnerProfile, leg: str | None) -> str:
        """
        1-й личный → внешняя нога пригласившего (как у него у аплайна).
        Со 2-го → явный выбор left/right, иначе противоположная нога.
        """
        outer_leg = sponsor.binary_placement.leg or LEG_LEFT
        personal_count = SponsorLink.objects.filter(sponsor=sponsor).count()
        if personal_count <= FIRST_PERSONAL_INVITE_COUNT:
            return outer_leg
        if leg in (LEG_LEFT, LEG_RIGHT):
            return leg
        return LEG_RIGHT if outer_leg == LEG_LEFT else LEG_LEFT

    @staticmethod
    def _find_first_free_slot(
        sponsor: PartnerProfile,
        leg: str,
    ) -> tuple[PartnerProfile, str, int]:
        sponsor_placement = BinaryPlacement.objects.get(partner=sponsor)

        if not BinaryPlacement.objects.filter(parent=sponsor, leg=leg).exists():
            return sponsor, leg, sponsor_placement.depth + 1

        direct_child = BinaryPlacement.objects.select_related("partner").get(
            parent=sponsor,
            leg=leg,
        )
        queue = deque([direct_child.partner])

        while queue:
            node = queue.popleft()
            node_placement = BinaryPlacement.objects.get(partner=node)

            if not BinaryPlacement.objects.filter(parent=node, leg=leg).exists():
                return node, leg, node_placement.depth + 1

            child = BinaryPlacement.objects.select_related("partner").get(
                parent=node,
                leg=leg,
            )
            queue.append(child.partner)

        return sponsor, leg, sponsor_placement.depth + 1

    @staticmethod
    def _place_as_root(partner: PartnerProfile) -> BinaryPlacement:
        return BinaryPlacementService._create_placement(
            partner,
            parent=None,
            leg=LEG_LEFT,
            depth=0,
        )

    @staticmethod
    def _create_placement(
        partner: PartnerProfile,
        *,
        parent: PartnerProfile | None,
        leg: str,
        depth: int,
    ) -> BinaryPlacement:
        now = timezone.now()
        placement = BinaryPlacement.objects.create(
            partner=partner,
            parent=parent,
            leg=leg,
            depth=depth,
            placed_at=now,
        )
        partner.placed_at = now
        partner.save(update_fields=["placed_at", "updated_at"])
        return placement


class PartnerActivationService:
    @staticmethod
    @transaction.atomic
    def on_tariff_purchase(user: User, product, order) -> PartnerProfile:
        partner = PartnerActivationService._get_or_create_profile(user)
        ActivityService.sync_from_subscription(partner)
        PartnerActivationService._ensure_sponsor_link(partner)
        PartnerActivationService._ensure_binary_balance(partner)
        BinaryPlacementService.place_if_needed(partner)
        return partner

    @staticmethod
    def on_tariff_upgrade(user: User, product, order) -> PartnerProfile | None:
        partner = PartnerActivationService._get_existing_profile(user)
        if not partner:
            return None
        ActivityService.sync_from_subscription(partner)
        return partner

    @staticmethod
    def on_renewal(user: User, order) -> PartnerProfile | None:
        partner = PartnerActivationService._get_existing_profile(user)
        if not partner:
            return None
        ActivityService.sync_from_subscription(partner)
        ActivityService.set_frozen(partner, frozen=False)
        return partner

    @staticmethod
    def _get_or_create_profile(user: User) -> PartnerProfile:
        partner, _ = PartnerProfile.objects.get_or_create(
            user=user,
            defaults={
                "invited_by_id": user.invited_by_id,
                "current_rank": DEFAULT_RANK,
                "highest_rank": DEFAULT_RANK,
            },
        )
        return partner

    @staticmethod
    def _get_existing_profile(user: User) -> PartnerProfile | None:
        return PartnerProfile.objects.filter(user=user).first()

    @staticmethod
    def _ensure_sponsor_link(partner: PartnerProfile) -> SponsorLink | None:
        existing = SponsorLink.objects.filter(partner=partner).first()
        if existing:
            return existing

        sponsor = get_sponsor_partner(partner)
        if not sponsor:
            return None

        return SponsorLink.objects.create(
            partner=partner,
            sponsor=sponsor,
            placed_at=timezone.now(),
        )

    @staticmethod
    def _ensure_binary_balance(partner: PartnerProfile) -> BinaryBalance:
        balance, _ = BinaryBalance.objects.get_or_create(partner=partner)
        return balance
