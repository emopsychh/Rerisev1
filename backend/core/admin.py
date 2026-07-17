from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import StackedInline, TabularInline

__all__ = ["ModelAdmin", "StackedInline", "TabularInline"]


class ModelAdmin(UnfoldModelAdmin):
    """Базовый admin с кратким описанием раздела на русском."""

    section_description = ""
    list_before_template = "admin/section_description.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        if self.section_description:
            extra_context.setdefault("subtitle", self.section_description)
        return super().changelist_view(request, extra_context=extra_context)
