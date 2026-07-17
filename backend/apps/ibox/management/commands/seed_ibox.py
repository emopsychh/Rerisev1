from django.core.management.base import BaseCommand

from apps.ibox.constants import CATEGORY_CONTENT, CATEGORY_DESIGN, CATEGORY_SALES
from apps.ibox.models import Scenario

SCENARIOS = [
    {
        "slug": "selling-post",
        "title": "Создать продающий пост",
        "category": CATEGORY_CONTENT,
        "token_cost": 10,
        "sort_order": 0,
        "description": "Пост для соцсетей с оффером и CTA",
        "prompt_template": (
            "Ты копирайтер RE:RISE. Напиши продающий пост на русском. "
            "Структура: хук → боль → решение → CTA. Без воды."
        ),
    },
    {
        "slug": "content-plan-7",
        "title": "Контент-план на 7 дней",
        "category": CATEGORY_CONTENT,
        "token_cost": 15,
        "sort_order": 1,
        "description": "План публикаций на неделю",
        "prompt_template": (
            "Составь контент-план на 7 дней: тема, формат, хук, CTA. "
            "Ответ таблицей в markdown."
        ),
    },
    {
        "slug": "reels-script",
        "title": "Сценарий Reels",
        "category": CATEGORY_CONTENT,
        "token_cost": 12,
        "sort_order": 2,
        "description": "Короткий сценарий под вертикальное видео",
        "prompt_template": (
            "Напиши сценарий Reels 30–45 сек: хук 3 сек, тело, CTA. "
            "Укажи текст на экране и речь."
        ),
    },
    {
        "slug": "commercial-offer",
        "title": "Коммерческое предложение",
        "category": CATEGORY_SALES,
        "token_cost": 20,
        "sort_order": 3,
        "description": "КП под клиента или нишу",
        "prompt_template": (
            "Составь коммерческое предложение: проблема, решение, пакеты, цена, "
            "гарантия, следующий шаг. Тон деловой, ясный."
        ),
    },
    {
        "slug": "cold-message",
        "title": "Холодное сообщение",
        "category": CATEGORY_SALES,
        "token_cost": 8,
        "sort_order": 4,
        "description": "Первое касание в мессенджере",
        "prompt_template": (
            "Напиши короткое холодное сообщение (до 500 знаков): персонализация, "
            "ценность, мягкий CTA. Без спама."
        ),
    },
    {
        "slug": "objection-reply",
        "title": "Ответ на возражение",
        "category": CATEGORY_SALES,
        "token_cost": 10,
        "sort_order": 5,
        "description": "Скрипт ответа клиенту",
        "prompt_template": (
            "Клиент возражает. Дай 2–3 варианта ответа: эмпатия, переформулировка, "
            "доказательство, вопрос дальше."
        ),
    },
    {
        "slug": "landing-outline",
        "title": "Структура лендинга",
        "category": CATEGORY_SALES,
        "token_cost": 18,
        "sort_order": 6,
        "description": "Блоки посадочной страницы",
        "prompt_template": (
            "Собери структуру лендинга: hero, боли, решение, соцдоказательства, "
            "оффер, FAQ, CTA. Для каждого блока — заголовок и 2–3 буллета."
        ),
    },
    {
        "slug": "midjourney-prompt",
        "title": "Промпт для Midjourney",
        "category": CATEGORY_DESIGN,
        "token_cost": 8,
        "sort_order": 7,
        "description": "Промпт под визуал продукта",
        "prompt_template": (
            "Сгенерируй 3 промпта Midjourney на английском: subject, style, lighting, "
            "composition, --ar. Кратко поясни каждый на русском."
        ),
    },
    {
        "slug": "presentation-outline",
        "title": "Презентация продукта",
        "category": CATEGORY_DESIGN,
        "token_cost": 16,
        "sort_order": 8,
        "description": "Слайды и тезисы",
        "prompt_template": (
            "Составь outline презентации на 8–10 слайдов: заголовок слайда + тезисы. "
            "Фокус на выгоде, не на фичах."
        ),
    },
    {
        "slug": "brand-visual-brief",
        "title": "Бриф на визуал",
        "category": CATEGORY_DESIGN,
        "token_cost": 12,
        "sort_order": 9,
        "description": "Бриф для дизайнера / AI-картинки",
        "prompt_template": (
            "Собери креативный бриф: цель, аудитория, moodboard-слова, цвета, "
            "что нельзя, deliverables."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed iBox scenarios (10 mock scenarios)"

    def handle(self, *args, **options):
        for item in SCENARIOS:
            scenario, created = Scenario.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    **item,
                    "is_active": True,
                    "default_model": "gpt-4o-mini",
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} scenario: {scenario.slug}")

        self.stdout.write(
            self.style.SUCCESS(f"iBox seed complete: {Scenario.objects.count()} scenarios")
        )
