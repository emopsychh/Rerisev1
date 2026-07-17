CATEGORY_CONTENT = "content"
CATEGORY_SALES = "sales"
CATEGORY_DESIGN = "design"

SCENARIO_CATEGORY_CHOICES = [
    (CATEGORY_CONTENT, "Контент"),
    (CATEGORY_SALES, "Продажи"),
    (CATEGORY_DESIGN, "Дизайн"),
]

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"

MESSAGE_ROLE_CHOICES = [
    (ROLE_USER, "Пользователь"),
    (ROLE_ASSISTANT, "Ассистент"),
    (ROLE_SYSTEM, "Система"),
]

REASON_PURCHASE = "purchase"
REASON_GENERATION = "generation"
REASON_BONUS = "bonus"
REASON_ADMIN = "admin"
REASON_TARIFF = "tariff"
REASON_REFUND = "refund"

TOKEN_REASON_CHOICES = [
    (REASON_PURCHASE, "Покупка"),
    (REASON_GENERATION, "Генерация"),
    (REASON_BONUS, "Бонус"),
    (REASON_ADMIN, "Админ"),
    (REASON_TARIFF, "По тарифу"),
    (REASON_REFUND, "Возврат"),
]

DEFAULT_MODEL = "gpt-4o-mini"
PROVIDER_MOCK = "mock"
PROVIDER_OPENAI = "openai"
