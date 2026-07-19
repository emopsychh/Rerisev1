import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-in-production")

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

# Во время manage.py test проверка тарифов должна работать (locked и т.п.).
_RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"
if _RUNNING_TESTS:
    ACADEMY_OPEN_ACCESS = False
else:
    ACADEMY_OPEN_ACCESS = (
        os.getenv("ACADEMY_OPEN_ACCESS", "false").lower() == "true"
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Behind nginx / TLS terminator
if os.getenv("DJANGO_BEHIND_PROXY", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "apps.users",
    "apps.commerce",
    "apps.partner",
    "apps.ledger",
    "apps.wallet",
    "apps.academy",
    "apps.content",
    "apps.ibox",
    "apps.crm",
    "apps.admin_ops",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "rerise"),
        "USER": os.getenv("POSTGRES_USER", "rerise"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "rerise"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Видео через админку — до 500 МБ (как client_max_body_size в nginx).
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS
if not DEBUG and CORS_ALLOWED_ORIGINS:
    CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ReRise API",
    "DESCRIPTION": (
        "Backend API для кабинета RE:RISE.\n\n"
        "Auth: JWT Bearer (`POST /api/v1/auth/login`).\n"
        "Ошибки бизнес-правил: HTTP 422, код `BUSINESS_RULE_ERROR`.\n"
        "Staff-операции: `/api/v1/admin/*` (IsAdminUser)."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Auth", "description": "Регистрация и JWT"},
        {"name": "Users", "description": "Профиль и уведомления"},
        {"name": "Store", "description": "Тарифы и заказы"},
        {"name": "Partner", "description": "Партнёрский кабинет"},
        {"name": "Wallet", "description": "Баланс и вывод"},
        {"name": "Academy", "description": "Обучение"},
        {"name": "Content", "description": "Home, материалы, чаты"},
        {"name": "AI Hub", "description": "Сценарии, сессии и токены AI Hub"},
        {"name": "CRM", "description": "Канбан лидов"},
        {"name": "Admin", "description": "Staff-операции"},
    ],
}

RERISE_PUBLIC_ID_PREFIX = "RERISE"
RERISE_REFERRAL_BASE_URL = os.getenv(
    "RERISE_REFERRAL_BASE_URL", "https://rerise.app/join"
)

PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "manual")
MANUAL_PAYMENT_TTL_MINUTES = int(os.getenv("MANUAL_PAYMENT_TTL_MINUTES", "60"))
MANUAL_PAYMENT_INSTRUCTIONS = os.getenv(
    "MANUAL_PAYMENT_INSTRUCTIONS",
    "Заказ #{order_id} на ${amount_usd}. Оплатите USDT и дождитесь подтверждения администратором.",
)
ACTIVITY_DAYS_PER_MONTH = int(os.getenv("ACTIVITY_DAYS_PER_MONTH", "30"))
RENEWAL_WINDOW_DAYS = int(os.getenv("RENEWAL_WINDOW_DAYS", "7"))

# AI Hub gateway: mock (default) | openai
IBOX_AI_PROVIDER = os.getenv("IBOX_AI_PROVIDER", "mock")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# CryptoBot / Crypto Pay
CRYPTOBOT_API_TOKEN = os.getenv("CRYPTOBOT_API_TOKEN", "")
CRYPTOBOT_TESTNET = os.getenv("CRYPTOBOT_TESTNET", "false").lower() == "true"
CRYPTOBOT_WEBHOOK_SECRET_PATH = os.getenv("CRYPTOBOT_WEBHOOK_SECRET_PATH", "dev-webhook-secret")
CRYPTOBOT_ASSET = os.getenv("CRYPTOBOT_ASSET", "USDT")
CRYPTOBOT_INVOICE_TTL_MINUTES = int(os.getenv("CRYPTOBOT_INVOICE_TTL_MINUTES", "60"))
CRYPTOBOT_PAID_BTN_URL = os.getenv(
    "CRYPTOBOT_PAID_BTN_URL",
    "https://rerise.app/market?order={order_id}",
)

# Celery — без брокера в тестах/локально: eager
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = (
    os.getenv("CELERY_TASK_ALWAYS_EAGER", "true" if not CELERY_BROKER_URL else "false").lower()
    == "true"
)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rerise-default",
    }
}
REDIS_URL = os.getenv("REDIS_URL", "")
if REDIS_URL:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }

UNFOLD = {
    "SITE_TITLE": "Админка RE:RISE",
    "SITE_HEADER": "RE:RISE",
    "SITE_SUBHEADER": "Панель управления",
    "SITE_SYMBOL": "dashboard",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
}
