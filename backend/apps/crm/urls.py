from django.urls import path

from apps.crm.views import LeadDetailView, LeadListCreateView

urlpatterns = [
    path("crm/leads", LeadListCreateView.as_view(), name="crm-leads"),
    path("crm/leads/<int:lead_id>", LeadDetailView.as_view(), name="crm-lead-detail"),
]
