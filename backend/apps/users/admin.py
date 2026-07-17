from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group

from core.admin import ModelAdmin
from apps.admin_ops.services import UserModerationService
from apps.users.models import Notification, NotificationSettings, Profile, ReferralCode, User

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    section_description = "Группы прав доступа для сотрудников админки. Через них выдают роли: кто может править курсы, платежи, выводы и т.п."


@admin.register(User)
class UserAdmin(ModelAdmin):
    section_description = "Учётные записи людей в системе. Здесь можно найти пользователя, заблокировать доступ или снова его открыть."
    list_display = ("email", "phone", "is_active", "is_staff", "created_at")
    search_fields = ("email", "phone", "profile__public_id")
    list_filter = ("is_active", "is_staff", "created_at")
    actions = ["block_users", "unblock_users"]
    readonly_fields = ("created_at", "updated_at", "last_login_at")

    @admin.action(description="Заблокировать пользователей")
    def block_users(self, request, queryset):
        blocked = 0
        for user in queryset:
            if user.pk == request.user.pk:
                self.message_user(request, "Нельзя заблокировать себя", messages.ERROR)
                continue
            UserModerationService.block(user, actor=request.user, reason="admin_action")
            blocked += 1
        if blocked:
            self.message_user(request, f"Заблокировано: {blocked}", messages.SUCCESS)

    @admin.action(description="Разблокировать пользователей")
    def unblock_users(self, request, queryset):
        unblocked = 0
        for user in queryset:
            UserModerationService.unblock(user, actor=request.user)
            unblocked += 1
        if unblocked:
            self.message_user(request, f"Разблокировано: {unblocked}", messages.SUCCESS)


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    section_description = "Публичные данные человека: имя, страна, язык интерфейса и публичный ID в кабинете."
    list_display = ("public_id", "first_name", "last_name", "language", "country")
    search_fields = ("public_id", "first_name", "last_name", "user__email")
    list_filter = ("language",)


@admin.register(ReferralCode)
class ReferralCodeAdmin(ModelAdmin):
    section_description = "Личные пригласительные коды. По ним новые люди попадают в структуру партнёра."
    list_display = ("code", "user", "is_active")
    search_fields = ("code", "user__email")
    list_filter = ("is_active",)


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(ModelAdmin):
    section_description = "Какие уведомления человек хочет получать: на почту и/или push."
    list_display = ("user", "email_enabled", "push_enabled")
    search_fields = ("user__email",)


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    section_description = "Сообщения внутри кабинета: бонусы, доступ, система, CRM. Можно проверить, что ушло пользователю."
    list_display = ("user", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("user__email", "title")
