from django.core.management.base import BaseCommand

from apps.content.constants import (
    CHAT_TYPE_INVITE,
    CHAT_TYPE_OPEN,
    CHAT_TYPE_SERVICE,
    FILE_TYPE_DOC,
    FILE_TYPE_FLOW,
    FILE_TYPE_PDF,
    FILE_TYPE_PROMPT,
)
from apps.content.models import (
    Banner,
    MaterialCategory,
    MaterialFile,
    MaterialGroup,
    TelegramChat,
)
from apps.content.services import MaterialCatalogService

BANNERS = [
    {
        "sort_order": 0,
        "title": "2 ЧАСТЬ ChatGPT New",
        "subtitle": "Новые сценарии для контента и продаж",
        "image_url": "/media/banners/gpt-new.jpg",
        "tags": ["Контент", "Продажи", "Автоматизация"],
        "link_url": "/programs/gpt-new",
    },
    {
        "sort_order": 1,
        "title": "AI Design — стартуй сейчас",
        "subtitle": "Генерация визуалов для соцсетей и офферов",
        "image_url": "/media/banners/ai-design.jpg",
        "tags": ["Дизайн", "HIT"],
        "link_url": "/programs/ai-design",
    },
]

CATEGORIES = [
    {"slug": "ai-box", "name": "AI Hub", "icon": "ibox", "sort_order": 0},
    {"slug": "sales", "name": "Продажи", "icon": "sales", "sort_order": 1},
    {"slug": "content", "name": "Контент", "icon": "content", "sort_order": 2},
    {"slug": "partner", "name": "Партнёрство", "icon": "partner", "sort_order": 3},
]

GROUPS = [
    {
        "category": "ai-box",
        "sort_order": 0,
        "title": "Промпты",
        "description": "Готовые промпты для ежедневной работы",
        "file_type": FILE_TYPE_PROMPT,
        "required_tariff": "rise",
        "files": [
            {
                "title": "Промпт для продающего поста",
                "format": "TXT",
                "file_url": "/media/materials/prompt-sales-post.txt",
                "file_size": 2048,
            },
            {
                "title": "Промпт для коммерческого предложения",
                "format": "TXT",
                "file_url": "/media/materials/prompt-offer.txt",
                "file_size": 3072,
            },
            {
                "title": "Промпт для сценария Reels",
                "format": "TXT",
                "file_url": "/media/materials/prompt-reels.txt",
                "file_size": 2560,
            },
        ],
    },
    {
        "category": "ai-box",
        "sort_order": 1,
        "title": "Flows",
        "description": "Многошаговые сценарии в AI Hub",
        "file_type": FILE_TYPE_FLOW,
        "required_tariff": "rise-pro",
        "files": [
            {
                "title": "Flow: контент на неделю",
                "format": "JSON",
                "file_url": "/media/materials/flow-week.json",
                "file_size": 4096,
            },
            {
                "title": "Flow: оффер + креатив",
                "format": "JSON",
                "file_url": "/media/materials/flow-offer.json",
                "file_size": 3584,
            },
        ],
    },
    {
        "category": "sales",
        "sort_order": 0,
        "title": "Шаблоны продаж",
        "description": "Офферы, КП и follow-up письма",
        "file_type": FILE_TYPE_DOC,
        "required_tariff": "rise",
        "files": [
            {
                "title": "Шаблон коммерческого предложения",
                "format": "DOCX",
                "file_url": "/media/materials/sales-offer.docx",
                "file_size": 18432,
            },
            {
                "title": "Follow-up после созвона",
                "format": "DOCX",
                "file_url": "/media/materials/sales-followup.docx",
                "file_size": 12288,
            },
        ],
    },
    {
        "category": "sales",
        "sort_order": 1,
        "title": "Скрипты",
        "description": "Скрипты звонков и переписок",
        "file_type": FILE_TYPE_PDF,
        "required_tariff": "rise-pro",
        "files": [
            {
                "title": "Скрипт холодного касания",
                "format": "PDF",
                "file_url": "/media/materials/script-cold.pdf",
                "file_size": 65536,
            },
            {
                "title": "Скрипт закрытия сделки",
                "format": "PDF",
                "file_url": "/media/materials/script-close.pdf",
                "file_size": 73728,
            },
        ],
    },
    {
        "category": "content",
        "sort_order": 0,
        "title": "Контент-планы",
        "description": "Планы публикаций на неделю и месяц",
        "file_type": FILE_TYPE_DOC,
        "required_tariff": "rise",
        "files": [
            {
                "title": "Контент-план на 7 дней",
                "format": "XLSX",
                "file_url": "/media/materials/content-plan-7.xlsx",
                "file_size": 24576,
            },
            {
                "title": "Контент-план на месяц",
                "format": "XLSX",
                "file_url": "/media/materials/content-plan-30.xlsx",
                "file_size": 32768,
            },
        ],
    },
    {
        "category": "content",
        "sort_order": 1,
        "title": "Посты",
        "description": "Готовые тексты постов и сторис",
        "file_type": FILE_TYPE_PROMPT,
        "required_tariff": "rise",
        "files": [
            {
                "title": "Серия постов: экспертиза",
                "format": "TXT",
                "file_url": "/media/materials/posts-expertise.txt",
                "file_size": 5120,
            },
            {
                "title": "Серия сторис: прогрев",
                "format": "TXT",
                "file_url": "/media/materials/stories-warmup.txt",
                "file_size": 4608,
            },
        ],
    },
    {
        "category": "partner",
        "sort_order": 0,
        "title": "Партнёрские материалы",
        "description": "Презентации и гайды для команды",
        "file_type": FILE_TYPE_PDF,
        "required_tariff": "rise",
        "files": [
            {
                "title": "Презентация RE:RISE",
                "format": "PDF",
                "file_url": "/media/materials/partner-deck.pdf",
                "file_size": 204800,
            },
            {
                "title": "Гайд по приглашению",
                "format": "PDF",
                "file_url": "/media/materials/partner-invite.pdf",
                "file_size": 98304,
            },
        ],
    },
    {
        "category": "partner",
        "sort_order": 1,
        "title": "Чек-листы",
        "description": "Чек-листы запуска и активации",
        "file_type": FILE_TYPE_PDF,
        "required_tariff": "rise-pro-max",
        "files": [
            {
                "title": "Чек-лист первого месяца",
                "format": "PDF",
                "file_url": "/media/materials/checklist-month1.pdf",
                "file_size": 40960,
            },
            {
                "title": "Чек-лист квалификации",
                "format": "PDF",
                "file_url": "/media/materials/checklist-qualify.pdf",
                "file_size": 36864,
            },
        ],
    },
]

CHATS = [
    {
        "sort_order": 0,
        "title": "Чат партнёров",
        "description": "Общение, вопросы, кейсы и обмен опытом",
        "chat_type": CHAT_TYPE_OPEN,
        "telegram_url": "https://t.me/rerise_partners",
        "min_rank": None,
        "access_requirement": None,
    },
    {
        "sort_order": 1,
        "title": "Чат новичков",
        "description": "Онбординг, первые шаги и ответы на базовые вопросы",
        "chat_type": CHAT_TYPE_OPEN,
        "telegram_url": "https://t.me/rerise_newbies",
        "min_rank": None,
        "access_requirement": None,
    },
    {
        "sort_order": 2,
        "title": "Чат лидеров",
        "description": "Стратегия, метрики, координация запусков",
        "chat_type": CHAT_TYPE_INVITE,
        "telegram_url": "https://t.me/rerise_leaders",
        "min_rank": "partner_2",
        "access_requirement": "Партнёр II и выше",
    },
    {
        "sort_order": 3,
        "title": "Чат экспертов",
        "description": "Глубокая практика, разборы и менторство",
        "chat_type": CHAT_TYPE_INVITE,
        "telegram_url": "https://t.me/rerise_experts",
        "min_rank": "expert_1",
        "access_requirement": "Эксперт I и выше",
    },
    {
        "sort_order": 4,
        "title": "Поддержка RE:RISE",
        "description": "Сервисный чат по доступу, оплате и техническим вопросам",
        "chat_type": CHAT_TYPE_SERVICE,
        "telegram_url": "https://t.me/rerise_support",
        "min_rank": None,
        "access_requirement": None,
    },
    {
        "sort_order": 5,
        "title": "Канал маркетинга",
        "description": "Готовые посты, визуалы, новости запусков и сценарии продвижения.",
        "chat_type": CHAT_TYPE_OPEN,
        "telegram_url": "https://t.me/rerise_marketing",
        "min_rank": None,
        "access_requirement": None,
    },
]


class Command(BaseCommand):
    help = "Seed content: banners, 8 material sections, 5 telegram chats"

    def handle(self, *args, **options):
        for item in BANNERS:
            banner, created = Banner.objects.update_or_create(
                title=item["title"],
                defaults={**item, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} banner: {banner.title}")

        categories_by_slug = {}
        for item in CATEGORIES:
            category, created = MaterialCategory.objects.update_or_create(
                slug=item["slug"],
                defaults=item,
            )
            categories_by_slug[category.slug] = category
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} category: {category.slug}")

        for group_item in GROUPS:
            data = dict(group_item)
            files_data = data.pop("files")
            category_slug = data.pop("category")
            category = categories_by_slug[category_slug]

            group, created = MaterialGroup.objects.update_or_create(
                category=category,
                title=data["title"],
                defaults={
                    "description": data.get("description"),
                    "file_type": data["file_type"],
                    "required_tariff": data.get("required_tariff"),
                    "sort_order": data["sort_order"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} group: {group.title}")

            for index, file_data in enumerate(files_data):
                MaterialFile.objects.update_or_create(
                    group=group,
                    title=file_data["title"],
                    defaults={
                        "file_url": file_data["file_url"],
                        "file_size": file_data.get("file_size"),
                        "format": file_data["format"],
                        "sort_order": index,
                    },
                )

            MaterialCatalogService.refresh_group_file_count(group)

        for item in CHATS:
            chat, created = TelegramChat.objects.update_or_create(
                title=item["title"],
                defaults={**item, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} chat: {chat.title}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Content seed complete: "
                f"{Banner.objects.count()} banners, "
                f"{MaterialGroup.objects.count()} groups, "
                f"{MaterialFile.objects.count()} files, "
                f"{TelegramChat.objects.count()} chats"
            )
        )
