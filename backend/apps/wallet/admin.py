from django.contrib import admin, messages

from core.admin import ModelAdmin
from apps.admin_ops.services import AuditLogger
from apps.wallet.constants import (
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_PENDING,
)
from apps.wallet.models import Balance, SavedAddress, WithdrawalRequest
from apps.wallet.services import WithdrawalService, WithdrawalValidationError


@admin.register(Balance)
class BalanceAdmin(ModelAdmin):
    section_description = "Денежный кошелёк пользователя: доступно к выводу, в ожидании и всего заработано."
    list_display = ("user", "available_usd", "pending_usd", "total_earned_usd", "updated_at")
    search_fields = ("user__email",)
    readonly_fields = ("updated_at",)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(ModelAdmin):
    section_description = "Заявки на вывод USDT. Здесь одобряют, отклоняют или отмечают выплату после перевода."
    list_display = (
        "id",
        "user",
        "amount_usd",
        "network",
        "status",
        "created_at",
    )
    list_filter = ("status", "network", "created_at")
    search_fields = ("user__email", "usdt_address", "tx_hash")
    readonly_fields = ("paid_at", "created_at", "updated_at")
    actions = ["approve_withdrawal", "reject_withdrawal", "mark_paid"]

    @admin.action(description="Одобрить вывод")
    def approve_withdrawal(self, request, queryset):
        approved = 0
        for withdrawal in queryset.select_related("user"):
            if withdrawal.status != WITHDRAWAL_STATUS_PENDING:
                continue
            try:
                WithdrawalService.approve(withdrawal, reviewed_by=request.user)
                AuditLogger.record(
                    actor=request.user,
                    action="withdrawal_approved",
                    target_type="withdrawal_request",
                    target_id=withdrawal.pk,
                    new_value={"status": WITHDRAWAL_STATUS_APPROVED},
                )
                approved += 1
            except WithdrawalValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)

        if approved:
            self.message_user(request, f"Одобрено заявок: {approved}", messages.SUCCESS)
        else:
            self.message_user(request, "Нет pending-заявок для одобрения", messages.WARNING)

    @admin.action(description="Отклонить вывод")
    def reject_withdrawal(self, request, queryset):
        rejected = 0
        for withdrawal in queryset.select_related("user"):
            try:
                WithdrawalService.reject(withdrawal, reviewed_by=request.user)
                AuditLogger.record(
                    actor=request.user,
                    action="withdrawal_rejected",
                    target_type="withdrawal_request",
                    target_id=withdrawal.pk,
                    new_value={"status": "rejected"},
                )
                rejected += 1
            except WithdrawalValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)

        if rejected:
            self.message_user(request, f"Отклонено заявок: {rejected}", messages.SUCCESS)

    @admin.action(description="Отметить как выплачено")
    def mark_paid(self, request, queryset):
        paid = 0
        for withdrawal in queryset.select_related("user"):
            try:
                WithdrawalService.mark_paid(withdrawal, reviewed_by=request.user)
                AuditLogger.record(
                    actor=request.user,
                    action="withdrawal_paid",
                    target_type="withdrawal_request",
                    target_id=withdrawal.pk,
                    new_value={"status": "paid"},
                )
                paid += 1
            except WithdrawalValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)

        if paid:
            self.message_user(
                request,
                f"Выплачено заявок: {paid}",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Нет заявок для выплаты",
                messages.WARNING,
            )


@admin.register(SavedAddress)
class SavedAddressAdmin(ModelAdmin):
    section_description = "Сохранённые крипто-адреса пользователей для вывода (сеть и адрес)."
    list_display = ("user", "network", "address", "is_default")
    list_filter = ("network", "is_default")
    search_fields = ("user__email", "address")
