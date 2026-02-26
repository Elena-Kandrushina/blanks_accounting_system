from django.db import models
from django.urls import reverse


class ProductCategory(models.Model):
    """Категория изделий"""

    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория изделий"
        verbose_name_plural = "Категории изделий"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель готового изделия"""

    article = models.CharField(max_length=50, unique=True, verbose_name="Артикул")
    name = models.CharField(max_length=200, verbose_name="Наименование")
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Категория",
    )

    description = models.TextField(blank=True, verbose_name="Описание")
    drawing = models.FileField(
        upload_to="products/drawings/", blank=True, null=True, verbose_name="Чертеж"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Изделие"
        verbose_name_plural = "Изделия"
        ordering = ["article"]

    def __str__(self):
        return f"{self.article} - {self.name}"

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"pk": self.pk})


class ConsumptionNorm(models.Model):
    """Норма расхода заготовок на изделие"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="consumption_norms"
    )
    blank = models.ForeignKey(
        "blanks.Blank", on_delete=models.PROTECT, related_name="used_in_products"
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Количество"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Норма расхода"
        verbose_name_plural = "Нормы расхода"
        unique_together = ("product", "blank")
        ordering = ["product", "blank"]

    def __str__(self):
        return f"{self.product.name} -> {self.blank.name}: {self.quantity}"
