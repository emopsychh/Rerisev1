from django.contrib import admin, messages

from core.admin import ModelAdmin
from apps.admin_ops.services import AuditLogger
from apps.commerce.models import Order, Payment, Product, Subscription, TariffPlan, UserAccess
from apps.commerce.services import PaymentConfirmationService


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    section_description = "То, что продаём в магазине: тарифы, подписка, токены, отдельные программы. Здесь задают цену и активность."
    list_display = ("slug", "name", "type", "price_usd", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("slug", "name")


@admin.register(TariffPlan)
class TariffPlanAdmin(ModelAdmin):
    section_description = "Условия конкретного тарифа: PV, глубина бинара, бонусы, стартовые токены. Это «начинка» тарифного продукта."
    list_display = (
        "tariff_id",
        "product",
        "personal_bonus_cap_usd",
        "purchase_pv_cap",
        "binary_depth",
    )
    search_fields = ("tariff_id", "product__name")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    section_description = "Заказы из кабинета: покупка, продление, апгрейд. Смотрите статус и сумму — это «чеки» пользователей."
    list_display = ("id", "user", "product", "amount_usd", "status", "order_type", "created_at")
    list_filter = ("status", "order_type", "created_at")
    search_fields = ("user__email", "product__slug")
    readonly_fields = ("paid_at", "created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    section_description = "Платежи по заказам. Если оплата ручная — здесь подтверждают поступление денег (действие «Подтвердить платёж»)."
    list_display = ("id", "order", "provider", "amount_usd", "status", "created_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("external_id", "order__id", "order__user__email")
    readonly_fields = ("paid_at", "created_at", "updated_at")
    actions = ["confirm_payment"]

    @admin.action(description="Подтвердить платёж (вручную)")
    def confirm_payment(self, request, queryset):
        confirmed = 0
        for payment in queryset.select_related("order"):
            if payment.status != "pending":
                continue
            order = PaymentConfirmationService.confirm(payment)
            AuditLogger.record(
                actor=request.user,
                action="payment_confirmed",
                target_type="payment",
                target_id=payment.pk,
                new_value={"order_id": order.pk, "status": "paid"},
            )
            confirmed += 1

        if confirmed:
            self.message_user(
                request,
                f"Подтверждено платежей: {confirmed}",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Нет pending-платежей для подтверждения",
                messages.WARNING,
            )


@admin.register(UserAccess)
class UserAccessAdmin(ModelAdmin):
    section_description = "Что именно открыто человеку после оплаты: доступ к продукту, срок действия, активен ли он сейчас."
    list_display = ("user", "product", "is_active", "granted_at", "expires_at")
    list_filter = ("is_active", "product__type")
    search_fields = ("user__email", "product__slug")


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    section_description = "Активность партнёра по тарифу: до какой даты действует и включено ли автопродление."
    list_display = ("user", "tariff_id", "active_until", "auto_renew")
    list_filter = ("tariff_id", "auto_renew")
    search_fields = ("user__email", "tariff_id")
