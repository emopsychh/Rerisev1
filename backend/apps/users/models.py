from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Телефон", max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    is_staff = models.BooleanField("Доступ к админке", default=False)
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitees",
        verbose_name="Пригласивший",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    last_login_at = models.DateTimeField("Последний вход", null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = "users_user"

    def __str__(self):
        return self.email


class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ("ru", "Русский"),
        ("en", "Английский"),
        ("es", "Испанский"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь"
    )
    first_name = models.CharField("Имя", max_length=100, blank=True)
    last_name = models.CharField("Фамилия", max_length=100, blank=True)
    avatar_url = models.URLField("URL аватара", max_length=500, blank=True)
    country = models.CharField("Страна", max_length=100, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)
    language = models.CharField(
        "Язык", max_length=5, choices=LANGUAGE_CHOICES, default="ru"
    )
    public_id = models.CharField(
        "Публичный ID",
        max_length=20,
        unique=True,
        help_text="Уникальный идентификатор для ссылок",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        db_table = "users_profile"

    def __str__(self):
        return self.public_id


class ReferralCode(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="referral_code",
        verbose_name="Пользователь",
    )
    code = models.CharField("Код", max_length=32, unique=True)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Реферальный код"
        verbose_name_plural = "Реферальные коды"
        db_table = "users_referral_code"

    def __str__(self):
        return self.code


class NotificationSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_settings",
        verbose_name="Пользователь",
    )
    email_enabled = models.BooleanField("Email-уведомления", default=True)
    push_enabled = models.BooleanField("Push-уведомления", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Настройки уведомлений"
        verbose_name_plural = "Настройки уведомлений"
        db_table = "users_notification_settings"


class Notification(models.Model):
    TYPE_CHOICES = [
        ("bonus", "Бонус"),
        ("access", "Доступ"),
        ("system", "Система"),
        ("crm", "CRM"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications", verbose_name="Пользователь"
    )
    type = models.CharField("Тип", max_length=50, choices=TYPE_CHOICES, default="system")
    title = models.CharField("Заголовок", max_length=255)
    body = models.TextField("Текст", blank=True)
    is_read = models.BooleanField("Прочитано", default=False)
    metadata = models.JSONField(
        "Метаданные",
        default=dict,
        blank=True,
        help_text='{"key": "value"}',
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        db_table = "users_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]
