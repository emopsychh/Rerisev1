from django.contrib import admin

from core.admin import ModelAdmin
from apps.admin_ops.models import AuditLog, SystemConfig


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    section_description = "Кто из сотрудников что сделал в админке: подтвердил платёж, заблокировал пользователя и т.п. Только чтение."
    list_display = (
        "id",
        "created_at",
        "actor",
        "action",
        "target_type",
        "target_id",
    )
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("action", "actor__email", "target_type")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "old_value",
        "new_value",
        "ip_address",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemConfig)
class SystemConfigAdmin(ModelAdmin):
    section_description = "Технические ключи и настройки системы. Меняйте только если понимаете, за что отвечает ключ."
    list_display = ("key", "description")
    search_fields = ("key", "description")
