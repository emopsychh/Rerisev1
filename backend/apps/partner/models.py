from django.conf import settings
from django.db import models

from apps.partner.constants import DEFAULT_RANK, LEG_CHOICES


class PartnerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="partner_profile",
        verbose_name="Пользователь",
    )
    tariff_id = models.CharField("ID тарифа", max_length=20, blank=True, null=True)
    is_active = models.BooleanField("Активен", default=False)
    activity_until = models.DateTimeField("Активность до", null=True, blank=True)
    tariff_lost_at = models.DateTimeField("Тариф потерян", null=True, blank=True)
    current_rank = models.CharField("Текущий ранг", max_length=50, default=DEFAULT_RANK)
    highest_rank = models.CharField("Максимальный ранг", max_length=50, default=DEFAULT_RANK)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_partners",
        verbose_name="Пригласивший",
    )
    placed_at = models.DateTimeField("Размещён", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Партнёрский профиль"
        verbose_name_plural = "Партнёрские профили"
        db_table = "partner_profile"
        indexes = [
            models.Index(fields=["invited_by"]),
            models.Index(fields=["tariff_id"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["current_rank"]),
        ]

    def __str__(self):
        return f"Partner {self.user_id} ({self.tariff_id or 'no tariff'})"


class SponsorLink(models.Model):
    partner = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="sponsor_link",
        verbose_name="Партнёр",
    )
    sponsor = models.ForeignKey(
        PartnerProfile,
        on_delete=models.PROTECT,
        related_name="personal_invites",
        verbose_name="Спонсор",
    )
    placed_at = models.DateTimeField("Размещён")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Связь со спонсором"
        verbose_name_plural = "Связи со спонсорами"
        db_table = "partner_sponsor_link"

    def __str__(self):
        return f"SponsorLink {self.partner_id} → {self.sponsor_id}"


class BinaryPlacement(models.Model):
    partner = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="binary_placement",
        verbose_name="Партнёр",
    )
    parent = models.ForeignKey(
        PartnerProfile,
        on_delete=models.PROTECT,
        related_name="binary_children",
        null=True,
        blank=True,
        verbose_name="Родитель",
    )
    leg = models.CharField("Плечо", max_length=5, choices=LEG_CHOICES)
    depth = models.PositiveSmallIntegerField("Глубина")
    placed_at = models.DateTimeField("Размещён")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Бинарное размещение"
        verbose_name_plural = "Бинарные размещения"
        db_table = "partner_binary_placement"
        indexes = [
            models.Index(fields=["parent", "leg"]),
            models.Index(fields=["depth"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "leg"],
                condition=models.Q(parent__isnull=False),
                name="partner_binary_unique_parent_leg",
            ),
        ]

    def __str__(self):
        return f"Binary {self.partner_id} under {self.parent_id} ({self.leg})"


class BinaryBalance(models.Model):
    partner = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="binary_balance",
        verbose_name="Партнёр",
    )
    left_pv = models.PositiveIntegerField("PV слева", default=0)
    right_pv = models.PositiveIntegerField("PV справа", default=0)
    is_frozen = models.BooleanField("Заморожен", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Бинарный баланс"
        verbose_name_plural = "Бинарные балансы"
        db_table = "partner_binary_balance"

    def __str__(self):
        return f"BinaryBalance {self.partner_id}"


class QualificationWeek(models.Model):
    partner = models.ForeignKey(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="qualification_weeks",
        verbose_name="Партнёр",
    )
    week_start = models.DateField("Начало недели")
    collapsed_pv = models.PositiveIntegerField("Схлопнутый PV", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Квалификационная неделя"
        verbose_name_plural = "Квалификационные недели"
        db_table = "partner_qualification_week"
        constraints = [
            models.UniqueConstraint(
                fields=["partner", "week_start"],
                name="partner_qualification_week_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["partner", "week_start"]),
        ]

    def __str__(self):
        return f"Week {self.week_start} · {self.partner_id}: {self.collapsed_pv} PV"


class RankHistory(models.Model):
    partner = models.ForeignKey(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="rank_history",
        verbose_name="Партнёр",
    )
    rank = models.CharField("Ранг", max_length=50)
    premium_usd = models.DecimalField("Премия, USD", max_digits=12, decimal_places=2, default=0)
    achieved_at = models.DateTimeField("Достигнут")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "История ранга"
        verbose_name_plural = "История рангов"
        db_table = "partner_rank_history"
        indexes = [
            models.Index(fields=["partner", "achieved_at"]),
        ]

    def __str__(self):
        return f"RankHistory {self.partner_id} → {self.rank}"


class FastStart(models.Model):
    partner = models.OneToOneField(
        PartnerProfile,
        on_delete=models.CASCADE,
        related_name="fast_start",
        verbose_name="Партнёр",
    )
    window_start = models.DateTimeField("Окно с")
    window_end = models.DateTimeField("Окно до")
    qualified_count = models.PositiveSmallIntegerField("Квалифицировано", default=0)
    reward_paid = models.BooleanField("Награда выплачена", default=False)
    reward_paid_at = models.DateTimeField("Дата выплаты награды", null=True, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Быстрый старт"
        verbose_name_plural = "Быстрые старты"
        db_table = "partner_fast_start"

    def __str__(self):
        return f"FastStart {self.partner_id} ({self.qualified_count}/4)"
