from django.contrib import admin

from core.admin import ModelAdmin, TabularInline
from apps.crm.models import Lead, LeadActivity, LeadStage


@admin.register(LeadStage)
class LeadStageAdmin(ModelAdmin):
    section_description = "Колонки канбана CRM: «новый», «в работе», «успех» и т.д. Порядок и цвет задают вид доски."
    list_display = ("slug", "name", "color", "sort_order")
    ordering = ("sort_order",)


class LeadActivityInline(TabularInline):
    model = LeadActivity
    extra = 0
    readonly_fields = ("action", "details", "created_by", "created_at")


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    section_description = "Карточки лидов партнёров: контакт, этап, сумма. Основная рабочая сущность CRM."
    list_display = ("name", "owner", "stage", "source", "value_usd", "updated_at")
    list_filter = ("stage", "source")
    search_fields = ("name", "owner__email", "contact", "phone")
    inlines = [LeadActivityInline]


@admin.register(LeadActivity)
class LeadActivityAdmin(ModelAdmin):
    section_description = "История действий по лиду: кто что менял и когда. Обычно смотрят из карточки лида."
    list_display = ("lead", "action", "created_by", "created_at")
    list_filter = ("action",)
