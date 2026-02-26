from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User с email вместо username"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Модель пользователя"""

    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        help_text="Загрузите фото",
    )

    ROLE_CHOICES = [
        ("admin", "Администратор"),
        ("technologist", "Технолог"),
        ("storekeeper", "Кладовщик"),
        ("production_master", "Мастер участка"),
        ("otk_senior", "Старший контролер ОТК"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="production_worker",
        verbose_name="Должность",
        help_text="Выберите должность пользователя",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Участок/Цех",
        help_text="Например: Участок №1, Склад готовой продукции",
    )

    is_approved = models.BooleanField(
        default=False,
        verbose_name="Подтвержден",
        help_text="Пользователь подтвержден администратором",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_administrator(self):
        return self.role == "admin" or self.is_superuser

    @property
    def is_technologist(self):
        return self.role == "technologist"

    @property
    def is_storekeeper(self):
        return self.role == "storekeeper"

    @property
    def is_production_master(self):
        return self.role == "production_master"

    @property
    def is_otk_senior(self):
        return self.role == "otk_senior"

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != "admin":
            self.role = "admin"
        super().save(*args, **kwargs)
