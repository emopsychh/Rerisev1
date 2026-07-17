from django.conf import settings
from django.db import models

from apps.wallet.constants import (
    NETWORK_CHOICES,
    WITHDRAWAL_STATUS_CHOICES,
    WITHDRAWAL_STATUS_PENDING,
)


class Balance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet_balance",
        verbose_name="Пользователь",
    )
    available_usd = models.DecimalField("Доступно, USD", max_digits=12, decimal_places=2, default=0)
    pending_usd = models.DecimalField("В ожидании, USD", max_digits=12, decimal_places=2, default=0)
    total_earned_usd = models.DecimalField(
        "Всего заработано, USD", max_digits=12, decimal_places=2, default=0
    )
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Баланс"
        verbose_name_plural = "Балансы"
        db_table = "wallet_balance"

    def __str__(self):
        return f"Wallet {self.user_id}: ${self.available_usd}"


class WithdrawalRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawal_requests",
        verbose_name="Пользователь",
    )
    amount_usd = models.DecimalField("Сумма, USD", max_digits=12, decimal_places=2)
    usdt_address = models.CharField("USDT-адрес", max_length=128)
    network = models.CharField("Сеть", max_length=20, choices=NETWORK_CHOICES)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=WITHDRAWAL_STATUS_CHOICES,
        default=WITHDRAWAL_STATUS_PENDING,
    )
    fee_usd = models.DecimalField("Комиссия, USD", max_digits=12, decimal_places=2, default=0)
    tx_hash = models.CharField("Хеш транзакции", max_length=128, blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_withdrawals",
        verbose_name="Проверил",
    )
    paid_at = models.DateTimeField("Выплачен", null=True, blank=True)
    rejection_reason = models.TextField("Причина отклонения", blank=True, null=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Заявка на вывод"
        verbose_name_plural = "Заявки на вывод"
        db_table = "wallet_withdrawal_request"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"Withdrawal {self.id} ${self.amount_usd} ({self.status})"


class SavedAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_addresses",
        verbose_name="Пользователь",
    )
    address = models.CharField("Адрес", max_length=128)
    network = models.CharField("Сеть", max_length=20, choices=NETWORK_CHOICES)
    is_default = models.BooleanField("По умолчанию", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Сохранённый адрес"
        verbose_name_plural = "Сохранённые адреса"
        db_table = "wallet_saved_address"
        constraints = [
            models.UniqueConstraint(fields=["user", "network"], name="wallet_saved_address_user_network"),
        ]
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        return f"{self.network}: {self.address[:12]}..."
