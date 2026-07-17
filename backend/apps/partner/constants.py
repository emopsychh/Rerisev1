DEFAULT_RANK = "partner_1"

RANK_LABELS = {
    "partner_1": "Партнёр I",
    "partner_2": "Партнёр II",
    "partner_3": "Партнёр III",
    "visionary": "Визионер",
}

HISTORICAL_RANK_NOTE = "Сохраняется независимо от активности"

INACTIVITY_INFO = (
    "После окончания активности тариф сохраняется 12 месяцев. "
    "Заработанный бинарный доход сохраняется, но новые начисления приостанавливаются."
)

LEG_LEFT = "left"
LEG_RIGHT = "right"
LEG_CHOICES = [
    (LEG_LEFT, "Левое"),
    (LEG_RIGHT, "Правое"),
]

DEFAULT_SECOND_PERSONAL_LEG = LEG_LEFT
DEFAULT_PARTNER_NAME = "Партнёр"

FIRST_PERSONAL_INVITE_COUNT = 1
