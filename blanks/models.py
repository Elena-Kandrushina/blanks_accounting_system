from django.db import models
from django.urls import reverse


class BlankCategory(models.Model):
    """Категория заготовок"""

    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория заготовок"
        verbose_name_plural = "Категории заготовок"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Blank(models.Model):
    """Модель заготовки"""

    UNIT_CHOICES = [
        ("шт", "Штуки"),
        ("кг", "Килограммы"),
        ("м", "Метры"),
        ("м2", "Метры квадратные"),
        ("м3", "Метры кубические"),
        ("компл", "Комплекты"),
    ]

    article = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    name = models.CharField(max_length=200, verbose_name="Наименование")
    category = models.ForeignKey(
        "BlankCategory",
        on_delete=models.SET_NULL,
        related_name="blanks",
        verbose_name="Категория",
        null=True,
        blank=True,
    )

    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default="шт",
        verbose_name="Единица измерения",
    )
    weight = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Вес, кг"
    )

    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заготовка"
        verbose_name_plural = "Заготовки"
        ordering = ["article"]

    def __str__(self):
        return f"{self.article} - {self.name}"

    def get_absolute_url(self):
        return reverse("blanks:blank_detail", kwargs={"pk": self.pk})
