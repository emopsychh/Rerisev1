FILE_TYPE_PROMPT = "PROMPT"
FILE_TYPE_PDF = "PDF"
FILE_TYPE_DOC = "DOC"
FILE_TYPE_VIDEO = "VIDEO"
FILE_TYPE_FLOW = "FLOW"

FILE_TYPE_CHOICES = [
    (FILE_TYPE_PROMPT, "Промпт"),
    (FILE_TYPE_PDF, "PDF"),
    (FILE_TYPE_DOC, "DOC"),
    (FILE_TYPE_VIDEO, "Видео"),
    (FILE_TYPE_FLOW, "Сценарий"),
]

CHAT_TYPE_OPEN = "open"
CHAT_TYPE_INVITE = "invite"
CHAT_TYPE_SERVICE = "service"

CHAT_TYPE_CHOICES = [
    (CHAT_TYPE_OPEN, "Открытый"),
    (CHAT_TYPE_INVITE, "По приглашению"),
    (CHAT_TYPE_SERVICE, "Служебный"),
]

CATEGORY_ALL = "all"
CATEGORY_FILTER_CHOICES = (
    CATEGORY_ALL,
    "ai-box",
    "sales",
    "content",
    "partner",
)

# Reuse academy tariff levels for material groups
TARIFF_MATERIAL_ACCESS = {
    "rise": 1,
    "rise-pro": 2,
    "rise-pro-max": 3,
}
