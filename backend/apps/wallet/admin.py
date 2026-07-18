from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import admin, messages

from core.admin import ModelAdmin
from apps.admin_ops.services import AdminAdjustmentService, AuditLogger
from apps.ledger.constants import DIRECTION_CREDIT, DIRECTION_DEBIT
from apps.ledger.services import LedgerError
from apps.wallet.constants import (
    WITHDRAWAL_STATUS_APPROVED,
    WITHDRAWAL_STATUS_PENDING,
)
from apps.wallet.models import Balance, SavedAddress, WithdrawalRequest
from apps.wallet.services import WithdrawalService, WithdrawalValidationError


class BalanceAdminForm(forms.ModelForm):
    credit_usd = forms.DecimalField(
        label="Начислить USD",
        required=False,
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        help_text="Создаст проводку в журнале. Баланс сам пересчитается.",
    )
    debit_usd = forms.DecimalField(
        label="Списать USD",
        required=False,
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        help_text="Списание с доступного баланса через журнал.",
    )
    adjustment_reason = forms.CharField(
        label="Причина корректировки",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Обязательна, если начисляете или списываете.",
    )

    class Meta:
        model = Balance
        fields = ("user",)


@admin.register(Balance)
class BalanceAdmin(ModelAdmin):
    section_description = (
        "Баланс считается из журнала (ledger), а не правится руками. "
        "Чтобы добавить средства пользователю — укажите сумму в поле «Начислить USD» и причину."
    )
    form = BalanceAdminForm
    list_display = ("user", "available_usd", "pending_usd", "total_earned_usd", "updated_at")
    search_fields = ("user__email",)
    readonly_fields = ("available_usd", "pending_usd", "total_earned_usd", "updated_at")
    fields = (
        "user",
        "available_usd",
        "pending_usd",
        "total_earned_usd",
        "credit_usd",
        "debit_usd",
        "adjustment_reason",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("user", "available_usd", "pending_usd", "total_earned_usd", "updated_at")
        return ("available_usd", "pending_usd", "total_earned_usd", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        credit = form.cleaned_data.get("credit_usd")
        debit = form.cleaned_data.get("debit_usd")
        reason = (form.cleaned_data.get("adjustment_reason") or "").strip()

        if credit and debit:
            messages.error(request, "Укажите либо начисление, либо списание — не оба сразу.")
            return

        if not credit and not debit:
            messages.info(
                request,
                "Баланс не менялся. Чтобы добавить средства, заполните «Начислить USD» и причину.",
            )
            return

        if not reason:
            messages.error(request, "Укажите причину корректировки.")
            return

        try:
            if credit:
                amount = Decimal(str(credit))
                AdminAdjustmentService.apply(
                    obj.user,
                    amount_usd=amount,
                    direction=DIRECTION_CREDIT,
                    reason=reason,
                    actor=request.user,
                )
                messages.success(request, f"Начислено ${amount} пользователю {obj.user.email}")
            else:
                amount = Decimal(str(debit))
                AdminAdjustmentService.apply(
                    obj.user,
                    amount_usd=amount,
                    direction=DIRECTION_DEBIT,
                    reason=reason,
                    actor=request.user,
                )
                messages.success(request, f"Списано ${amount} у пользователя {obj.user.email}")
        except (LedgerError, InvalidOperation) as exc:
            messages.error(request, str(exc))


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
