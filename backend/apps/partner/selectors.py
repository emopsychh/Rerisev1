from apps.commerce.selectors import get_tariff_display_name
from apps.partner.constants import (
    DEFAULT_PARTNER_NAME,
    HISTORICAL_RANK_NOTE,
    INACTIVITY_INFO,
    RANK_LABELS,
)
from apps.partner.models import PartnerProfile, SponsorLink


def get_partner_profile(user_id: int) -> PartnerProfile | None:
    return PartnerProfile.objects.filter(user_id=user_id).first()


def resolve_partner_profile(user) -> PartnerProfile | None:
    try:
        return user.partner_profile
    except PartnerProfile.DoesNotExist:
        return None


def user_is_partner(user) -> bool:
    partner = resolve_partner_profile(user)
    if partner is None and hasattr(user, "pk"):
        partner = get_partner_profile(user.pk)
    return bool(partner and partner.tariff_id)


def get_sponsor_partner(partner: PartnerProfile) -> PartnerProfile | None:
    if not partner.invited_by_id:
        return None
    return PartnerProfile.objects.filter(user_id=partner.invited_by_id).first()


def get_personal_invites(partner: PartnerProfile):
    return (
        SponsorLink.objects.filter(sponsor=partner)
        .select_related("partner__user__profile")
        .order_by("placed_at")
    )


def format_partner_name(profile) -> str:
    first = profile.first_name.strip()
    last = profile.last_name.strip()
    if first and last:
        return f"{first} {last[0]}."
    if first:
        return first
    if last:
        return f"{last[0]}."
    return DEFAULT_PARTNER_NAME


def get_rank_label(rank_id: str) -> str:
    return RANK_LABELS.get(rank_id, rank_id)


def serialize_invited_partner(link: SponsorLink) -> dict:
    invited = link.partner
    user_profile = invited.user.profile
    tariff_name = get_tariff_display_name(invited.tariff_id) if invited.tariff_id else None
    return {
        "id": invited.user_id,
        "name": format_partner_name(user_profile),
        "tariff": tariff_name,
        "is_active": invited.is_active,
        "joined_at": link.placed_at,
    }


def build_partner_profile_payload(partner: PartnerProfile | None) -> dict | None:
    if not partner or not partner.tariff_id:
        return None

    return {
        "tariff_name": get_tariff_display_name(partner.tariff_id),
        "is_active": partner.is_active,
        "activity_until": partner.activity_until,
        "historical_rank": get_rank_label(partner.highest_rank),
        "historical_rank_note": HISTORICAL_RANK_NOTE,
        "inactivity_info": INACTIVITY_INFO,
    }
