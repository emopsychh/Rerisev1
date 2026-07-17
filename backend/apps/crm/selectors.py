from django.db.models import Prefetch, Q

from apps.crm.models import Lead, LeadStage


def serialize_lead(lead: Lead) -> dict:
    time_label = None
    if lead.scheduled_at:
        time_label = lead.scheduled_at.isoformat().replace("+00:00", "Z")
    elif lead.task:
        time_label = lead.task

    return {
        "id": lead.id,
        "name": lead.name,
        "source": lead.source,
        "task": lead.task,
        "time": time_label,
        "value_usd": float(lead.value_usd) if lead.value_usd is not None else None,
        "phone": lead.phone,
        "contact": lead.contact,
        "note": lead.note,
        "stage": lead.stage.slug,
        "scheduled_at": (
            lead.scheduled_at.isoformat().replace("+00:00", "Z")
            if lead.scheduled_at
            else None
        ),
    }


def build_kanban(user, stage_slug: str | None = None, search: str | None = None) -> dict:
    leads_qs = Lead.objects.filter(owner=user).select_related("stage")
    if search:
        leads_qs = leads_qs.filter(
            Q(name__icontains=search)
            | Q(contact__icontains=search)
            | Q(phone__icontains=search)
            | Q(note__icontains=search)
            | Q(source__icontains=search)
        )
    if stage_slug:
        leads_qs = leads_qs.filter(stage__slug=stage_slug)

    stages = LeadStage.objects.prefetch_related(
        Prefetch("leads", queryset=leads_qs.order_by("-created_at"))
    ).order_by("sort_order", "id")

    if stage_slug:
        stages = stages.filter(slug=stage_slug)

    return {
        "stages": [
            {
                "slug": stage.slug,
                "name": stage.name,
                "color": stage.color,
                "leads": [serialize_lead(lead) for lead in stage.leads.all()],
            }
            for stage in stages
        ]
    }


def get_owned_lead(user, lead_id: int) -> Lead | None:
    return (
        Lead.objects.filter(pk=lead_id, owner=user)
        .select_related("stage")
        .first()
    )
