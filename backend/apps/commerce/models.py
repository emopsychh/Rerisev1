from decimal import Decimal

from django.conf import settings
from django.db import models


class Product(models.Model):
    TYPE_TARIFF = "tariff"
    TYPE_SUBSCRIPTION = "subscription"
    TYPE_TOKENS = "tokens"
    TYPE_PROGRAM = "program"

    TYPE_CHOICES = [
        (TYPE_TARIFF, "Тариф"),
        (TYPE_SUBSCRIPTION, "Подписка"),
        (TYPE_TOKENS, "Токены"),
        (TYPE_PROGRAM, "Программа"),
    ]

    slug = models.CharField("Slug", max_length=50, unique=True)
    type = models.CharField("Тип", max_length=20, choices=TYPE_CHOICES)
    name = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    price_usd = models.DecimalField("Цена, USD", max_digits=12, decimal_places=2)
    is_active = models.BooleanField("Активен", default=True)
    metadata = models.JSONField(
        "Метаданные",
        default=dict,
        blank=True,
        help_text='{"key": "value"}',
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        db_table = "commerce_product"

    def __str__(self):
        return self.name


class TariffPlan(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="tariff_plan",
        verbose_name="Продукт",
    )
    tariff_id = models.CharField("ID тарифа", max_length=20, unique=True)
    included_months = models.PositiveSmallIntegerField("Месяцев в тарифе", default=1)
    personal_bonus_cap_usd = models.DecimalField(
        "Лимит личного бонуса, USD", max_digits=12, decimal_places=2
    )
    purchase_pv_cap = models.PositiveIntegerField("Лимит PV за покупку")
    binary_depth = models.PositiveSmallIntegerField("Глубина бинара")
    matching_lines = models.PositiveSmallIntegerField("Линий матчинга")
    quick_start_eligible = models.BooleanField("Участвует в Fast Start", default=False)
    initial_tokens = models.PositiveIntegerField("Начальные токены", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"
        db_table = "commerce_tariff_plan"

    def __str__(self):
        return self.tariff_id


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает оплаты"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_EXPIRED, "Истёк"),
        (STATUS_CANCELLED, "Отменён"),
        (STATUS_REFUNDED, "Возвращён"),
    ]

    TYPE_PURCHASE = "purchase"
    TYPE_UPGRADE = "upgrade"
    TYPE_RENEWAL = "renewal"

    ORDER_TYPE_CHOICES = [
        (TYPE_PURCHASE, "Покупка"),
        (TYPE_UPGRADE, "Апгрейд"),
        (TYPE_RENEWAL, "Продление"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="orders", verbose_name="Продукт"
    )
    amount_usd = models.DecimalField("Сумма, USD", max_digits=12, decimal_places=2)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    order_type = models.CharField("Тип заказа", max_length=20, choices=ORDER_TYPE_CHOICES)
    previous_tariff_id = models.CharField(
        "Предыдущий тариф",
        max_length=20,
        blank=True,
        null=True,
        help_text="При апгрейде — ID старого тарифа",
    )
    paid_at = models.DateTimeField("Оплачен", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        db_table = "commerce_order"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_EXPIRED = "expired"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидает оплаты"),
        (STATUS_PAID, "Оплачен"),
        (STATUS_EXPIRED, "Истёк"),
        (STATUS_FAILED, "Ошибка"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="payments", verbose_name="Заказ"
    )
    provider = models.CharField("Провайдер", max_length=50)
    external_id = models.CharField(
        "Внешний ID", max_length=255, blank=True, null=True, db_index=True
    )
    amount_usd = models.DecimalField("Сумма, USD", max_digits=12, decimal_places=2)
    currency_crypto = models.CharField("Криптовалюта", max_length=10, blank=True, null=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    payment_url = models.TextField("Ссылка на оплату", blank=True, null=True)
    instructions = models.TextField("Инструкции", blank=True)
    expires_at = models.DateTimeField("Истекает", null=True, blank=True)
    webhook_payload = models.JSONField(
        "Данные webhook",
        null=True,
        blank=True,
        help_text='{"event": "..."}',
    )
    paid_at = models.DateTimeField("Оплачен", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        db_table = "commerce_payment"
        indexes = [
            models.Index(fields=["provider", "status"]),
        ]

    def __str__(self):
        return f"Payment #{self.pk} ({self.provider}/{self.status})"


class UserAccess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accesses",
        verbose_name="Пользователь",
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="accesses", verbose_name="Продукт"
    )
    granted_at = models.DateTimeField("Выдан")
    expires_at = models.DateTimeField("Истекает", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    source_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_accesses",
        verbose_name="Заказ-источник",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Доступ пользователя"
        verbose_name_plural = "Доступы пользователей"
        db_table = "commerce_user_access"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["user", "product"]),
        ]

    def __str__(self):
        return f"Access {self.user_id} → {self.product.slug}"


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="Пользователь",
    )
    tariff_id = models.CharField("ID тарифа", max_length=20)
    active_until = models.DateTimeField("Активна до")
    last_renewal_at = models.DateTimeField("Последнее продление", null=True, blank=True)
    auto_renew = models.BooleanField("Автопродление", default=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        db_table = "commerce_subscription"

    def __str__(self):
        return f"Subscription {self.user_id} ({self.tariff_id})"

    @property
    def is_active(self) -> bool:
        from django.utils import timezone

        return self.active_until > timezone.now()
