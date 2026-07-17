from django.contrib import admin

from core.admin import ModelAdmin, TabularInline
from apps.content.models import (
    Banner,
    MaterialCategory,
    MaterialFile,
    MaterialGroup,
    TelegramChat,
)


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    section_description = "Рекламные баннеры для главной страницы кабинета: заголовок, картинка, период показа."
    list_display = ("title", "is_active", "sort_order", "active_from", "active_until")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")


class MaterialGroupInline(TabularInline):
    model = MaterialGroup
    extra = 0
    fields = ("sort_order", "title", "file_type", "file_count", "required_tariff")


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(ModelAdmin):
    section_description = "Разделы библиотеки материалов в кабинете. Внутри категории — группы файлов."
    list_display = ("slug", "name", "sort_order")
    search_fields = ("slug", "name")
    inlines = [MaterialGroupInline]


class MaterialFileInline(TabularInline):
    model = MaterialFile
    extra = 0
    fields = ("sort_order", "title", "format", "file_url", "file_size")


@admin.register(MaterialGroup)
class MaterialGroupAdmin(ModelAdmin):
    section_description = "Папки/наборы файлов внутри категории: презентации, документы и т.п."
    list_display = ("title", "category", "file_type", "file_count", "required_tariff", "sort_order")
    list_filter = ("file_type", "required_tariff", "category")
    search_fields = ("title", "category__slug")
    inlines = [MaterialFileInline]


@admin.register(MaterialFile)
class MaterialFileAdmin(ModelAdmin):
    section_description = "Конкретные файлы для скачивания: ссылка, формат, размер."
    list_display = ("title", "group", "format", "file_size")
    list_filter = ("format",)
    search_fields = ("title", "group__title")


@admin.register(TelegramChat)
class TelegramChatAdmin(ModelAdmin):
    section_description = "Ссылки на Telegram-чаты и каналы, которые показываем в кабинете (партнёрский, поддержка и др.)."
    list_display = ("title", "chat_type", "min_rank", "is_active", "sort_order")
    list_filter = ("chat_type", "is_active")
    search_fields = ("title",)
