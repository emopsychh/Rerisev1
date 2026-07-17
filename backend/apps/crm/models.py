from django.conf import settings
from django.db import models


class LeadStage(models.Model):
    slug = models.SlugField("Slug", max_length=20, unique=True)
    name = models.CharField("Название", max_length=100)
    color = models.CharField("Цвет", max_length=20)
    sort_order = models.SmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Этап лида"
        verbose_name_plural = "Этапы лидов"
        db_table = "crm_lead_stage"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class Lead(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crm_leads",
        verbose_name="Владелец",
    )
    name = models.CharField("Имя", max_length=255)
    source = models.CharField("Источник", max_length=100, blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    contact = models.CharField("Контакт", max_length=100, blank=True, null=True)
    stage = models.ForeignKey(
        LeadStage,
        on_delete=models.PROTECT,
        related_name="leads",
        verbose_name="Этап",
    )
    task = models.CharField("Задача", max_length=255, blank=True, null=True)
    note = models.TextField("Заметка", blank=True, null=True)
    value_usd = models.DecimalField(
        "Сумма, USD", max_digits=12, decimal_places=2, blank=True, null=True
    )
    scheduled_at = models.DateTimeField("Запланировано", blank=True, null=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"
        db_table = "crm_lead"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "stage"], name="crm_lead_owner_stage_idx"),
            models.Index(fields=["owner", "-created_at"], name="crm_lead_owner_created_idx"),
        ]

    def __str__(self):
        return self.name


class LeadActivity(models.Model):
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Лид",
    )
    action = models.CharField("Действие", max_length=100)
    details = models.TextField("Детали", blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_activities",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Активность по лиду"
        verbose_name_plural = "Активности по лидам"
        db_table = "crm_lead_activity"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead_id}: {self.action}"
