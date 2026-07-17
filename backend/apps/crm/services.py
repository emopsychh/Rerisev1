from django.db import transaction
from django.utils import timezone

from apps.crm.constants import ACTION_CREATED, ACTION_STAGE_CHANGED, ACTION_UPDATED
from apps.crm.models import Lead, LeadActivity, LeadStage
from apps.users.models import User


class LeadService:
    @staticmethod
    def _log(lead: Lead, action: str, user: User, details: str | None = None) -> None:
        LeadActivity.objects.create(
            lead=lead,
            action=action,
            details=details,
            created_by=user,
        )

    @staticmethod
    @transaction.atomic
    def create_lead(owner: User, data: dict) -> Lead:
        stage_slug = data.get("stage") or "new"
        stage = LeadStage.objects.filter(slug=stage_slug).first()
        if not stage:
            raise LookupError("Стадия не найдена")

        lead = Lead.objects.create(
            owner=owner,
            name=data["name"],
            source=data.get("source"),
            phone=data.get("phone"),
            contact=data.get("contact"),
            stage=stage,
            task=data.get("task"),
            note=data.get("note"),
            value_usd=data.get("value_usd"),
            scheduled_at=data.get("scheduled_at"),
        )
        LeadService._log(lead, ACTION_CREATED, owner, details=f"stage={stage.slug}")
        return lead

    @staticmethod
    @transaction.atomic
    def update_lead(lead: Lead, user: User, data: dict) -> Lead:
        old_stage = lead.stage.slug
        fields = []

        if "name" in data and data["name"] is not None:
            lead.name = data["name"]
            fields.append("name")
        for field in ("source", "phone", "contact", "task", "note"):
            if field in data:
                setattr(lead, field, data[field])
                fields.append(field)
        if "value_usd" in data:
            lead.value_usd = data["value_usd"]
            fields.append("value_usd")
        if "scheduled_at" in data:
            lead.scheduled_at = data["scheduled_at"]
            fields.append("scheduled_at")

        if "stage" in data and data["stage"]:
            stage = LeadStage.objects.filter(slug=data["stage"]).first()
            if not stage:
                raise LookupError("Стадия не найдена")
            lead.stage = stage
            fields.append("stage")

        if not fields:
            return lead

        lead.updated_at = timezone.now()
        fields.append("updated_at")
        lead.save(update_fields=fields)

        stage_changed = "stage" in fields and lead.stage.slug != old_stage
        other_fields = [f for f in fields if f not in ("stage", "updated_at")]

        if stage_changed:
            LeadService._log(
                lead,
                ACTION_STAGE_CHANGED,
                user,
                details=f"{old_stage} → {lead.stage.slug}",
            )
        if other_fields:
            LeadService._log(lead, ACTION_UPDATED, user, details=",".join(other_fields))
        elif not stage_changed:
            LeadService._log(lead, ACTION_UPDATED, user, details="updated_at")

        return lead

    @staticmethod
    @transaction.atomic
    def delete_lead(lead: Lead) -> None:
        lead.delete()
