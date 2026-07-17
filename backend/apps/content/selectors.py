from django.db.models import Count, Max, Prefetch, Q
from django.utils import timezone

from apps.academy.access import load_user_access_context
from apps.academy.models import Program
from apps.content.access import (
    chat_access_requirement_text,
    user_has_chat_access,
    user_has_material_group_access,
)
from apps.content.constants import CATEGORY_ALL
from apps.content.models import Banner, MaterialCategory, MaterialFile, MaterialGroup, TelegramChat


def get_active_banners():
    now = timezone.now()
    return (
        Banner.objects.filter(is_active=True)
        .filter(Q(active_from__isnull=True) | Q(active_from__lte=now))
        .filter(Q(active_until__isnull=True) | Q(active_until__gte=now))
        .order_by("sort_order", "id")
    )


def serialize_banner(banner: Banner) -> dict:
    return {
        "id": banner.id,
        "title": banner.title,
        "subtitle": banner.subtitle,
        "image_url": banner.image_url,
        "tags": banner.tags or [],
        "link_url": banner.link_url,
    }


def build_home_payload(user) -> dict:
    banners = [serialize_banner(banner) for banner in get_active_banners()]
    programs_count = Program.objects.filter(is_published=True).count()

    from apps.academy.constants import STATUS_IN_PROGRESS
    from apps.academy.models import UserProgress
    from apps.ibox.tokens import TokenService
    from apps.partner.engine_constants import rank_name
    from apps.partner.selectors import get_partner_profile
    from apps.commerce.selectors import get_user_subscription, subscription_can_renew

    continue_learning = None
    progress = (
        UserProgress.objects.filter(user=user, status=STATUS_IN_PROGRESS)
        .select_related("last_lesson__module__program", "program")
        .order_by("-updated_at")
        .first()
    )
    if progress and progress.last_lesson_id:
        lesson = progress.last_lesson
        continue_learning = {
            "program_slug": progress.program.slug,
            "program_title": progress.program.title,
            "lesson_id": lesson.id,
            "lesson_title": lesson.title,
            "module_title": lesson.module.title,
            "percent": progress.progress_percent,
        }

    partner = get_partner_profile(user.pk)
    subscription = get_user_subscription(user.pk)
    partner_summary = None
    can_renew = subscription_can_renew(subscription)
    if partner and partner.tariff_id:
        partner_summary = {
            "tariff_id": partner.tariff_id,
            "is_active": partner.is_active,
            "current_rank_name": rank_name(partner.current_rank),
            "can_renew": can_renew,
        }

    token_balance = TokenService.get_available(user)

    # Одно главное действие для главной
    if continue_learning:
        next_action = {
            "type": "continue_lesson",
            "title": "Продолжить обучение",
            "subtitle": continue_learning["lesson_title"],
            "link": f"/programs/{continue_learning['program_slug']}",
        }
    elif token_balance > 0:
        next_action = {
            "type": "open_ibox",
            "title": "Открыть AI Box",
            "subtitle": "Выберите сценарий или напишите задачу",
            "link": "/ibox",
        }
    elif can_renew:
        next_action = {
            "type": "renew",
            "title": "Продлить активность",
            "subtitle": "Сохраните доступ к кабинету партнёра",
            "link": "/partner/renew",
        }
    else:
        next_action = {
            "type": "browse_programs",
            "title": "Выберите программу",
            "subtitle": f"Доступно курсов: {programs_count}",
            "link": "/programs",
        }

    return {
        "banners": banners,
        "ai_box_widget": {
            "title": "RE:RISE AI — AI Box",
            "description": "Выберите сценарий или напишите задачу",
            "is_available": True,
            "token_balance": token_balance,
        },
        "programs_count": programs_count,
        "next_action": next_action,
        "continue_learning": continue_learning,
        "partner_summary": partner_summary,
        "token_balance": token_balance,
    }


def get_materials_queryset(category_slug: str | None = None, search: str | None = None):
    groups_qs = MaterialGroup.objects.order_by("sort_order", "id")
    if search:
        groups_qs = groups_qs.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(files__title__icontains=search)
        ).distinct()

    categories = MaterialCategory.objects.prefetch_related(
        Prefetch("groups", queryset=groups_qs)
    ).order_by("sort_order", "name")

    if category_slug and category_slug != CATEGORY_ALL:
        categories = categories.filter(slug=category_slug)

    return categories


def serialize_material_group(group: MaterialGroup) -> dict:
    return {
        "id": group.id,
        "title": group.title,
        "description": group.description,
        "file_type": group.file_type,
        "file_count": group.file_count,
        "last_updated": group.updated_at.isoformat().replace("+00:00", "Z"),
    }


def build_materials_catalog(user, category_slug: str | None = None, search: str | None = None) -> dict:
    access_context = load_user_access_context(user)
    categories = list(get_materials_queryset(category_slug, search))

    category_payload = []
    visible_group_ids = []

    for category in categories:
        groups_payload = []
        for group in category.groups.all():
            if not user_has_material_group_access(user, group, access_context=access_context):
                continue
            groups_payload.append(serialize_material_group(group))
            visible_group_ids.append(group.id)

        if groups_payload:
            category_payload.append(
                {
                    "slug": category.slug,
                    "name": category.name,
                    "groups": groups_payload,
                }
            )

    stats = MaterialFile.objects.filter(group_id__in=visible_group_ids).aggregate(
        total_files=Count("id"),
        last_updated=Max("updated_at"),
    )
    last_updated = stats["last_updated"]
    total_sections = (
        MaterialGroup.objects.filter(id__in=visible_group_ids).count()
        if visible_group_ids
        else 0
    )

    return {
        "stats": {
            "total_files": stats["total_files"] or 0,
            "total_sections": total_sections,
            "last_updated": (
                last_updated.isoformat().replace("+00:00", "Z") if last_updated else None
            ),
        },
        "categories": category_payload,
    }


def get_material_group_for_user(group_id: int, user) -> MaterialGroup | None:
    group = (
        MaterialGroup.objects.filter(pk=group_id)
        .select_related("category")
        .prefetch_related(
            Prefetch("files", queryset=MaterialFile.objects.order_by("sort_order", "id"))
        )
        .first()
    )
    if not group:
        return None
    if not user_has_material_group_access(user, group):
        return None
    return group


def serialize_material_group_detail(group: MaterialGroup) -> dict:
    return {
        "id": group.id,
        "title": group.title,
        "files": [
            {
                "id": file.id,
                "title": file.title,
                "format": file.format,
                "file_url": file.file_url,
                "file_size": file.file_size,
            }
            for file in group.files.all()
        ],
    }


def get_material_file_for_user(file_id: int, user) -> MaterialFile | None:
    material_file = (
        MaterialFile.objects.filter(pk=file_id)
        .select_related("group")
        .first()
    )
    if not material_file:
        return None
    if not user_has_material_group_access(user, material_file.group):
        return None
    return material_file


def build_chats_payload(user) -> dict:
    from apps.partner.models import PartnerProfile

    chats = TelegramChat.objects.filter(is_active=True).order_by("sort_order", "id")
    partner = PartnerProfile.objects.filter(user=user).first()
    payload = []
    community_active = False

    for chat in chats:
        accessible = user_has_chat_access(user, chat, partner=partner)
        if accessible:
            community_active = True
        item = {
            "id": chat.id,
            "title": chat.title,
            "description": chat.description,
            "chat_type": chat.chat_type,
            "telegram_url": chat.telegram_url if accessible else None,
            "is_accessible": accessible,
        }
        if not accessible:
            requirement = chat_access_requirement_text(chat)
            if requirement:
                item["access_requirement"] = requirement
        payload.append(item)

    return {
        "community_active": community_active,
        "chats": payload,
    }
