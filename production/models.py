from django.db import models
from django.conf import settings
from django.utils import timezone


class ProductionSite(models.Model):
    """Производственный участок"""

    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=20, unique=True, verbose_name="Код участка")
    warehouse = models.ForeignKey(
        "warehouse.Warehouse",
        on_delete=models.PROTECT,
        related_name="production_sites",
        verbose_name="Привязанный склад",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Производственный участок"
        verbose_name_plural = "Производственные участки"
        ordering = ["code"]

    def __str__(self):
        warehouse_info = f" ({self.warehouse.code})" if self.warehouse else ""
        return f"{self.code} - {self.name}{warehouse_info}"


class BlankReceipt(models.Model):
    """Заявка на выдачу заготовок на участок"""

    STATUS_CHOICES = [
        ("new", "Новая"),
        ("processing", "В обработке"),
        ("completed", "Выполнена"),
        ("cancelled", "Отменена"),
    ]

    number = models.CharField(max_length=50, unique=True, verbose_name="Номер заявки")
    production_site = models.ForeignKey(
        ProductionSite,
        on_delete=models.PROTECT,
        related_name="receipts",
        verbose_name="Участок",
    )
    blank = models.ForeignKey(
        "blanks.Blank", on_delete=models.PROTECT, verbose_name="Заготовка"
    )
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Количество"
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус"
    )

    receipt_date = models.DateTimeField(
        default=timezone.now, verbose_name="Дата заявки"
    )
    completed_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата выполнения"
    )

    source_info = models.CharField(
        max_length=200, blank=True, verbose_name="Откуда поступило"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_receipts",
        verbose_name="Создал",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_receipts",
        verbose_name="Обработал",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка на выдачу заготовок"
        verbose_name_plural = "Заявки на выдачу заготовок"
        ordering = ["-receipt_date"]

    def __str__(self):
        status_display = dict(self.STATUS_CHOICES).get(self.status, self.status)
        return f"{self.number} - {self.blank.name}: {self.quantity} ({status_display})"

    def save(self, *args, **kwargs):

        if not self.pk and not self.number:
            date_for_number = self.receipt_date or timezone.now()
            last_today = BlankReceipt.objects.filter(
                receipt_date__date=date_for_number.date()
            ).count()
            self.number = (
                f"REQ-{date_for_number.strftime('%Y%m%d')}-{last_today + 1:04d}"
            )

        super().save(*args, **kwargs)

    def process(self, user):
        """Обработка заявки кладовщиком"""
        if self.status != "new":
            return False, f"Заявка уже в статусе {self.get_status_display()}"

        from warehouse.models import StockBalance

        try:

            warehouse = self.production_site.warehouse
            if not warehouse:
                return False, "У участка не привязан склад"

            balance = StockBalance.objects.get(warehouse=warehouse, blank=self.blank)

            if balance.quantity < self.quantity:
                return (
                    False,
                    f"Недостаточно заготовок на складе. Доступно: {balance.quantity}",
                )

            balance.quantity -= self.quantity
            balance.save()

            from .models import SiteBalance

            site_balance, _ = SiteBalance.objects.get_or_create(
                production_site=self.production_site,
                blank=self.blank,
                defaults={"quantity": 0},
            )
            site_balance.quantity += self.quantity
            site_balance.save()

            from warehouse.models import StockMovement

            StockMovement.objects.create(
                movement_type="transfer",
                from_warehouse=warehouse,
                to_warehouse=None,
                to_production_site=self.production_site,
                blank=self.blank,
                quantity=self.quantity,
                movement_date=timezone.now(),
                reason=f"Выдача по заявке {self.number}",
                created_by=user,
            )

            self.status = "completed"
            self.completed_date = timezone.now()
            self.processed_by = user
            self.save()

            return True, "Заявка успешно выполнена"

        except StockBalance.DoesNotExist:
            return False, f"На складе нет заготовок {self.blank.name}"
        except Exception as e:
            return False, f"Ошибка при обработке заявки: {str(e)}"

    def cancel(self, user, reason=""):
        """Отмена заявки"""
        if self.status == "completed":
            return False, "Нельзя отменить выполненную заявку"

        self.status = "cancelled"
        self.comment = (self.comment or "") + f"\nОтменена: {reason}".strip()
        self.save()
        return True, "Заявка отменена"


class SiteBalance(models.Model):
    """Остатки заготовок на участке"""

    production_site = models.ForeignKey(
        ProductionSite, on_delete=models.PROTECT, related_name="balances"
    )
    blank = models.ForeignKey("blanks.Blank", on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Количество"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Остаток на участке"
        verbose_name_plural = "Остатки на участках"
        unique_together = ("production_site", "blank")

    def __str__(self):
        return f"{self.production_site.code} - {self.blank.name}: {self.quantity}"


class AssemblyReport(models.Model):
    """Отчет о сборке (списание заготовок)"""

    number = models.CharField(max_length=50, unique=True, verbose_name="Номер отчета")

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        verbose_name="Изделие",
        null=True,
        help_text="Какое изделие собиралось",
    )
    production_site = models.ForeignKey(
        "ProductionSite",
        on_delete=models.PROTECT,
        verbose_name="Участок",
        null=True,
        help_text="На каком участке производилась сборка",
    )

    report_date = models.DateField(default=timezone.now, verbose_name="Дата отчета")
    quantity = models.PositiveIntegerField(verbose_name="Собрано, шт")
    defect_quantity = models.PositiveIntegerField(default=0, verbose_name="Брак, шт")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    produced_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assembly_reports",
        verbose_name="Собрал",
    )

    class Meta:
        verbose_name = "Отчет о сборке"
        verbose_name_plural = "Отчеты о сборке"
        ordering = ["-report_date"]

    def __str__(self):
        product_name = self.product.name if self.product else "Не указано"
        return f"{self.number} - {product_name}: {self.quantity} шт."

    def save(self, *args, **kwargs):
        if not self.number:
            last_today = AssemblyReport.objects.filter(
                report_date=self.report_date
            ).count()
            self.number = (
                f"AR-{self.report_date.strftime('%Y%m%d')}-{last_today + 1:04d}"
            )

        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new:
            self.write_off_blanks()

    def get_required_blanks(self):
        """Получить список заготовок и их количество для данного отчета"""
        if not self.product:
            return {}

        required = {}
        norms = self.product.consumption_norms.all()
        for norm in norms:
            required[norm.blank] = norm.quantity * self.quantity
        return required

    def write_off_blanks(self):
        """Списание заготовок со склада участка на основании отчета"""
        if not self.product or not self.production_site:

            print(f"ОШИБКА: Для отчета {self.number} не указано изделие или участок")
            return

        required_blanks = self.get_required_blanks()

        if not required_blanks:
            print(f"ВНИМАНИЕ: Для изделия {self.product.name} не заданы нормы расхода")
            return

        for blank, total_used in required_blanks.items():
            try:
                balance = SiteBalance.objects.get(
                    production_site=self.production_site, blank=blank
                )

                balance.quantity -= total_used
                balance.save()

                from warehouse.models import StockMovement

                StockMovement.objects.create(
                    movement_type="write_off",
                    from_warehouse=self.production_site.warehouse,
                    blank=blank,
                    quantity=total_used,
                    movement_date=timezone.now(),
                    reason=f"Сборка изделий по отчету {self.number}",
                    created_by=self.produced_by,
                )

            except SiteBalance.DoesNotExist:

                from warehouse.models import StockMovement

                StockMovement.objects.create(
                    movement_type="write_off",
                    from_warehouse=self.production_site.warehouse,
                    blank=blank,
                    quantity=total_used,
                    movement_date=timezone.now(),
                    reason=f"Сборка изделий по отчету {self.number} (списание при отсутствии)",
                    created_by=self.produced_by,
                )
