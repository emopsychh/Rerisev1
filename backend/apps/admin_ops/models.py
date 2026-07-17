from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Автор",
    )
    action = models.CharField("Действие", max_length=100)
    target_type = models.CharField("Тип объекта", max_length=50)
    target_id = models.BigIntegerField("ID объекта", null=True, blank=True)
    old_value = models.JSONField(
        "Старое значение",
        null=True,
        blank=True,
        help_text='{"field": "value"}',
    )
    new_value = models.JSONField(
        "Новое значение",
        null=True,
        blank=True,
        help_text='{"field": "value"}',
    )
    ip_address = models.GenericIPAddressField("IP-адрес", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Журнал аудита"
        verbose_name_plural = "Журнал аудита"
        db_table = "admin_ops_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.target_type}:{self.target_id}"


class SystemConfig(models.Model):
    key = models.CharField("Ключ", max_length=100, unique=True)
    value = models.JSONField(
        "Значение",
        help_text='{"enabled": true}',
    )
    description = models.TextField("Описание", blank=True, null=True)

    class Meta:
        verbose_name = "Системная настройка"
        verbose_name_plural = "Системные настройки"
        db_table = "admin_ops_system_config"
        ordering = ["key"]

    def __str__(self):
        return self.key
