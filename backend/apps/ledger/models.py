from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.ledger.constants import (
    CURRENCY_CHOICES,
    CURRENCY_USD,
    DEBT_STATUS_CHOICES,
    DEBT_STATUS_OPEN,
    DIRECTION_CHOICES,
    DIRECTION_CREDIT,
    ENTRY_TYPES,
    ENTRY_TYPE_TITLES,
)


class RuleVersion(models.Model):
    version = models.CharField("Версия", max_length=20, unique=True)
    rules = models.JSONField(
        "Правила",
        help_text='{"withdrawal": {"min_usd": 100}}',
    )
    effective_from = models.DateTimeField("Действует с")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ledger_rule_versions",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Версия правил"
        verbose_name_plural = "Версии правил"
        db_table = "ledger_rule_version"
        ordering = ["-effective_from"]

    def __str__(self):
        return self.version


class Entry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
        verbose_name="Пользователь",
    )
    entry_type = models.CharField(
        "Тип проводки",
        max_length=50,
        choices=[(t, ENTRY_TYPE_TITLES[t]) for t in ENTRY_TYPES],
    )
    amount = models.DecimalField("Сумма", max_digits=14, decimal_places=4)
    currency = models.CharField(
        "Валюта", max_length=5, choices=CURRENCY_CHOICES, default=CURRENCY_USD
    )
    direction = models.CharField("Направление", max_length=10, choices=DIRECTION_CHOICES)
    source_type = models.CharField(
        "Тип источника", max_length=50, blank=True, null=True
    )
    source_id = models.BigIntegerField("ID источника", blank=True, null=True)
    rule_version = models.ForeignKey(
        RuleVersion,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Версия правил",
    )
    description = models.TextField("Описание", blank=True, null=True)
    metadata = models.JSONField(
        "Метаданные",
        default=dict,
        blank=True,
        help_text='{"key": "value"}',
    )
    idempotency_key = models.CharField(
        "Ключ идемпотентности",
        max_length=128,
        blank=True,
        null=True,
        unique=True,
        help_text="Уникальный ключ для предотвращения дублей",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Проводка"
        verbose_name_plural = "Проводки"
        db_table = "ledger_entry"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["entry_type", "-created_at"]),
            models.Index(fields=["source_type", "source_id"]),
            models.Index(fields=["currency", "user"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Ledger entries are immutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Ledger entries cannot be deleted")

    def __str__(self):
        return f"{self.entry_type} {self.direction} {self.amount} {self.currency}"


class AdjustmentDebt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adjustment_debts",
        verbose_name="Пользователь",
    )
    amount_usd = models.DecimalField("Сумма, USD", max_digits=12, decimal_places=2)
    remaining_usd = models.DecimalField("Остаток, USD", max_digits=12, decimal_places=2)
    reason = models.TextField("Причина")
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=DEBT_STATUS_CHOICES,
        default=DEBT_STATUS_OPEN,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_adjustment_debts",
        verbose_name="Создал",
    )
    resolved_at = models.DateTimeField("Закрыт", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Корректировочный долг"
        verbose_name_plural = "Корректировочные долги"
        db_table = "ledger_adjustment_debt"
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Debt {self.user_id} ${self.remaining_usd}"
