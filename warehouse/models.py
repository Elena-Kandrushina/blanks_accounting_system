from django.db import models
from django.conf import settings
from django.utils import timezone


class Warehouse(models.Model):
    """Склад (место хранения)"""

    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=20, unique=True, verbose_name="Код склада")
    address = models.CharField(
        max_length=200, blank=True, verbose_name="Адрес/Расположение"
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склады"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockBalance(models.Model):
    """Остатки заготовок на складе"""

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="balances"
    )
    blank = models.ForeignKey(
        "blanks.Blank", on_delete=models.PROTECT, related_name="stock_balances"
    )
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Количество"
    )
    min_stock = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Минимальный запас"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Остаток на складе"
        verbose_name_plural = "Остатки на складах"
        unique_together = ("warehouse", "blank")

    def __str__(self):
        return f"{self.warehouse.code} - {self.blank.name}: {self.quantity}"


class StockMovement(models.Model):
    """Движение заготовок"""

    MOVEMENT_TYPES = [
        ("receipt", "Поступление"),
        ("transfer", "Перемещение"),
        ("write_off", "Списание"),
        ("sale", "Продажа"),
    ]

    number = models.CharField(
        max_length=50, unique=True, verbose_name="Номер документа"
    )
    movement_type = models.CharField(
        max_length=20, choices=MOVEMENT_TYPES, verbose_name="Тип движения"
    )

    from_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="movements_from",
        null=True,
        blank=True,
        verbose_name="Откуда (склад)",
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="movements_to",
        null=True,
        blank=True,
        verbose_name="Куда (склад)",
    )

    to_production_site = models.ForeignKey(
        "production.ProductionSite",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Куда (участок)",
        help_text="Выберите участок для прямой передачи",
    )

    receipt_request = models.ForeignKey(
        "production.BlankReceipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Заявка на выдачу",
        help_text="Заявка, на основании которой создано движение",
    )

    blank = models.ForeignKey(
        "blanks.Blank", on_delete=models.PROTECT, verbose_name="Заготовка"
    )
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Количество"
    )

    movement_date = models.DateTimeField(verbose_name="Дата движения")
    reason = models.CharField(max_length=200, blank=True, verbose_name="Основание")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Движение заготовки"
        verbose_name_plural = "Движения заготовок"
        ordering = ["-movement_date"]

    def __str__(self):
        return f"{self.number} - {self.get_movement_type_display()}: {self.blank.name} {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.number:
            date_for_number = self.movement_date or timezone.now()
            last_today = StockMovement.objects.filter(
                movement_date__date=date_for_number.date()
            ).count()
            self.number = (
                f"MOV-{date_for_number.strftime('%Y%m%d')}-{last_today + 1:04d}"
            )
        super().save(*args, **kwargs)
