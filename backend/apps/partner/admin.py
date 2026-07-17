from django.contrib import admin

from core.admin import ModelAdmin
from apps.partner.models import (
    BinaryBalance,
    BinaryPlacement,
    FastStart,
    PartnerProfile,
    QualificationWeek,
    RankHistory,
    SponsorLink,
)


@admin.register(PartnerProfile)
class PartnerProfileAdmin(ModelAdmin):
    section_description = "Партнёрский статус человека: тариф, активность, текущий ранг. Это «карточка» в маркетинговом плане."
    list_display = (
        "user",
        "tariff_id",
        "is_active",
        "current_rank",
        "activity_until",
        "placed_at",
    )
    list_filter = ("is_active", "tariff_id", "current_rank")
    search_fields = ("user__email", "user__profile__public_id")


@admin.register(SponsorLink)
class SponsorLinkAdmin(ModelAdmin):
    section_description = "Кто кого пригласил (спонсорская линия). Нужно для бонусов и структуры."
    list_display = ("partner", "sponsor", "placed_at")
    search_fields = ("partner__user__email", "sponsor__user__email")


@admin.register(BinaryPlacement)
class BinaryPlacementAdmin(ModelAdmin):
    section_description = "Где человек стоит в бинарном дереве: родитель, нога (лево/право), глубина."
    list_display = ("partner", "parent", "leg", "depth", "placed_at")
    list_filter = ("leg", "depth")
    search_fields = ("partner__user__email", "parent__user__email")


@admin.register(BinaryBalance)
class BinaryBalanceAdmin(ModelAdmin):
    section_description = "PV слева и справа у партнёра, а также заморозка бинара при необходимости."
    list_display = ("partner", "left_pv", "right_pv", "is_frozen")


@admin.register(QualificationWeek)
class QualificationWeekAdmin(ModelAdmin):
    section_description = "Недельная квалификация: сколько PV «схлопнулось» за неделю у партнёра."
    list_display = ("partner", "week_start", "collapsed_pv")
    list_filter = ("week_start",)
    search_fields = ("partner__user__email",)


@admin.register(RankHistory)
class RankHistoryAdmin(ModelAdmin):
    section_description = "Когда человек получил ранг и какую премию за это начислили. История, а не редактор рангов."
    list_display = ("partner", "rank", "premium_usd", "achieved_at")
    list_filter = ("rank",)
    search_fields = ("partner__user__email",)


@admin.register(FastStart)
class FastStartAdmin(ModelAdmin):
    section_description = "Прогресс акции быстрого старта: сколько квалифицированных приглашений и выплачена ли награда."
    list_display = ("partner", "qualified_count", "reward_paid", "window_end")
    list_filter = ("reward_paid",)
    search_fields = ("partner__user__email",)
