from django.conf import settings
from django.db import models

from apps.ibox.constants import (
    DEFAULT_MODEL,
    MESSAGE_ROLE_CHOICES,
    SCENARIO_CATEGORY_CHOICES,
    TOKEN_REASON_CHOICES,
)


class Scenario(models.Model):
    slug = models.SlugField("Slug", max_length=100, unique=True)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True, null=True)
    category = models.CharField("Категория", max_length=50, choices=SCENARIO_CATEGORY_CHOICES)
    prompt_template = models.TextField("Шаблон промпта")
    default_model = models.CharField("Модель по умолчанию", max_length=50, default=DEFAULT_MODEL)
    token_cost = models.PositiveIntegerField("Стоимость в токенах", default=10)
    required_tariff = models.CharField(
        "Требуемый тариф", max_length=20, blank=True, null=True
    )
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.SmallIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Сценарий"
        verbose_name_plural = "Сценарии"
        db_table = "ibox_scenario"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ibox_sessions",
        verbose_name="Пользователь",
    )
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        verbose_name="Сценарий",
    )
    model = models.CharField("Модель", max_length=50, default=DEFAULT_MODEL)
    title = models.CharField("Название", max_length=255, blank=True, null=True)
    tokens_spent = models.PositiveIntegerField("Потрачено токенов", default=0)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Сессия чата"
        verbose_name_plural = "Сессии чатов"
        db_table = "ibox_chat_session"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="ibox_session_user_created"),
        ]

    def __str__(self):
        return self.title or f"Session #{self.pk}"


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Сессия",
    )
    role = models.CharField("Роль", max_length=20, choices=MESSAGE_ROLE_CHOICES)
    content = models.TextField("Содержимое")
    tokens_used = models.PositiveIntegerField("Использовано токенов", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чатов"
        db_table = "ibox_chat_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"], name="ibox_msg_session_created"),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"


class TokenBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ibox_token_balance",
        verbose_name="Пользователь",
    )
    available = models.PositiveIntegerField("Доступно", default=0)
    used_this_month = models.PositiveIntegerField("Использовано за месяц", default=0)
    month_reset_at = models.DateTimeField("Сброс месяца", blank=True, null=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Баланс токенов"
        verbose_name_plural = "Балансы токенов"
        db_table = "ibox_token_balance"

    def __str__(self):
        return f"{self.user_id}: {self.available}"


class TokenTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ibox_token_transactions",
        verbose_name="Пользователь",
    )
    amount = models.IntegerField("Сумма")
    reason = models.CharField("Причина", max_length=50, choices=TOKEN_REASON_CHOICES)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="token_transactions",
        verbose_name="Сессия",
    )
    order = models.ForeignKey(
        "commerce.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ibox_token_transactions",
        verbose_name="Заказ",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Операция с токенами"
        verbose_name_plural = "Операции с токенами"
        db_table = "ibox_token_transaction"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="ibox_tx_user_created"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.amount} ({self.reason})"
