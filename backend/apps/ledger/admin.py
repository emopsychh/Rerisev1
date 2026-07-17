from django.contrib import admin, messages

from core.admin import ModelAdmin
from apps.admin_ops.services import AdminAdjustmentService, AuditLogger
from apps.ledger.models import AdjustmentDebt, Entry, RuleVersion
from apps.ledger.services import LedgerError


@admin.register(RuleVersion)
class RuleVersionAdmin(ModelAdmin):
    section_description = "Версии правил начисления бонусов. Менять аккуратно: от версии зависят расчёты в журнале."
    list_display = ("version", "effective_from", "created_by", "created_at")
    search_fields = ("version",)
    list_filter = ("effective_from",)


@admin.register(Entry)
class EntryAdmin(ModelAdmin):
    section_description = "Финансовые проводки: начисления, списания, PV. Только просмотр — руками сюда не правят."
    list_display = (
        "id",
        "user",
        "entry_type",
        "amount",
        "currency",
        "direction",
        "created_at",
    )
    list_filter = ("entry_type", "currency", "direction", "created_at")
    search_fields = ("user__email", "idempotency_key", "description")
    readonly_fields = (
        "user",
        "entry_type",
        "amount",
        "currency",
        "direction",
        "source_type",
        "source_id",
        "rule_version",
        "description",
        "metadata",
        "idempotency_key",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdjustmentDebt)
class AdjustmentDebtAdmin(ModelAdmin):
    section_description = "Ручные корректировки и долги: если нужно удержать или учесть сумму вне обычных бонусов."
    list_display = ("user", "amount_usd", "remaining_usd", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "reason")
    readonly_fields = ("remaining_usd", "created_by", "created_at", "resolved_at")
    fields = (
        "user",
        "amount_usd",
        "remaining_usd",
        "reason",
        "status",
        "created_by",
        "resolved_at",
        "created_at",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ("remaining_usd", "created_by", "created_at", "resolved_at")
        return ("user", "amount_usd", "remaining_usd", "created_by", "created_at", "resolved_at")

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("user", "amount_usd", "reason")
        return self.fields

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            AuditLogger.record(
                actor=request.user,
                action="adjustment_debt_updated",
                target_type="adjustment_debt",
                target_id=obj.pk,
                new_value={"status": obj.status, "remaining_usd": str(obj.remaining_usd)},
            )
            return

        try:
            debt = AdminAdjustmentService.create_debt(
                obj.user,
                amount_usd=obj.amount_usd,
                reason=obj.reason,
                actor=request.user,
            )
        except LedgerError as exc:
            messages.error(request, str(exc))
            raise

        obj.pk = debt.pk
        obj.remaining_usd = debt.remaining_usd
        obj.status = debt.status
        obj.created_by = debt.created_by
        obj.created_at = debt.created_at
        messages.success(request, f"Создан корректировочный долг #{debt.pk}")
