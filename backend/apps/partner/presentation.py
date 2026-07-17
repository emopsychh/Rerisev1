from apps.partner.selectors import (
    build_partner_profile_payload,
    resolve_partner_profile,
    user_is_partner,
)


def partner_payload_for_user(user) -> dict | None:
    return build_partner_profile_payload(resolve_partner_profile(user))
