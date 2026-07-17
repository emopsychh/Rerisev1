# Progress statuses
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_CURRENT = "current"

PROGRESS_STATUS_CHOICES = [
    (STATUS_NOT_STARTED, "Не начат"),
    (STATUS_IN_PROGRESS, "В процессе"),
    (STATUS_COMPLETED, "Завершён"),
]

# Program list filters
FILTER_ALL = "all"
FILTER_OWNED = "owned"
FILTER_AVAILABLE = "available"
FILTER_COMPLETED = "completed"

PROGRAM_FILTER_CHOICES = [
    FILTER_ALL,
    FILTER_OWNED,
    FILTER_AVAILABLE,
    FILTER_COMPLETED,
]

# Access
ACCESS_OWNED = "owned"
ACCESS_IN_PROGRESS = "in_progress"
ACCESS_COMPLETED = "completed"
ACCESS_LOCKED = "locked"
ACCESS_AVAILABLE_FOR_PURCHASE = "available_for_purchase"

# Card actions
ACTION_OPEN = "open"
ACTION_CONTINUE = "continue"
ACTION_DETAILS = "details"

# Lesson types
LESSON_TYPE_VIDEO = "video"
LESSON_TYPE_PRACTICE = "practice"
LESSON_TYPE_READING = "reading"

LESSON_TYPE_CHOICES = [
    (LESSON_TYPE_VIDEO, "Видео"),
    (LESSON_TYPE_PRACTICE, "Практика"),
    (LESSON_TYPE_READING, "Чтение"),
]

# Resource types
RESOURCE_SUMMARY = "summary"
RESOURCE_TEMPLATE = "template"
RESOURCE_PRACTICE = "practice"
RESOURCE_FILE = "file"

RESOURCE_TYPE_CHOICES = [
    (RESOURCE_SUMMARY, "Конспект"),
    (RESOURCE_TEMPLATE, "Шаблон"),
    (RESOURCE_PRACTICE, "Практика"),
    (RESOURCE_FILE, "Файл"),
]

# Tariff access (preliminary, from 06-commerce-crypto.md)
TARIFF_ACADEMY_ACCESS = {
    "rise": 1,
    "rise-pro": 2,
    "rise-pro-max": 3,
}
