from django.urls import path

from apps.partner.views.partner import (
    InvitedPartnersView,
    PartnerDashboardView,
    PartnerRanksView,
    PartnerRenewView,
    PartnerStructureView,
)

urlpatterns = [
    path("partner/invited", InvitedPartnersView.as_view(), name="partner-invited"),
    path("partner/dashboard", PartnerDashboardView.as_view(), name="partner-dashboard"),
    path("partner/ranks", PartnerRanksView.as_view(), name="partner-ranks"),
    path("partner/structure", PartnerStructureView.as_view(), name="partner-structure"),
    path("partner/renew", PartnerRenewView.as_view(), name="partner-renew"),
]
