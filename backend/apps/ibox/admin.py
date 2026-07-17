from django.contrib import admin

from core.admin import ModelAdmin, TabularInline
from apps.ibox.models import ChatMessage, ChatSession, Scenario, TokenBalance, TokenTransaction


@admin.register(Scenario)
class ScenarioAdmin(ModelAdmin):
    section_description = "Сценарии AI Hub: готовые «режимы» чата, стоимость в токенах и активность."
    list_display = ("slug", "title", "category", "token_cost", "is_active", "sort_order")
    list_filter = ("category", "is_active")
    search_fields = ("slug", "title")


class ChatMessageInline(TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "tokens_used", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(ModelAdmin):
    section_description = "Диалоги пользователей с AI: какой сценарий, сколько токенов потрачено."
    list_display = ("id", "user", "scenario", "model", "tokens_spent", "created_at")
    list_filter = ("model",)
    search_fields = ("user__email", "title")
    inlines = [ChatMessageInline]


@admin.register(TokenBalance)
class TokenBalanceAdmin(ModelAdmin):
    section_description = "Сколько AI-токенов осталось у человека и сколько уже использовано в месяце."
    list_display = ("user", "available", "used_this_month", "updated_at")
    search_fields = ("user__email",)


@admin.register(TokenTransaction)
class TokenTransactionAdmin(ModelAdmin):
    section_description = "История списаний и начислений токенов: покупка пакета или расход на чат."
    list_display = ("user", "amount", "reason", "session", "order", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__email",)
