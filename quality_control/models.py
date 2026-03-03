from django.db import models
from django.conf import settings
from django.utils import timezone
from production.models import ProductionSite, SiteBalance


class DefectType(models.Model):
    """Справочник видов брака"""

    code = models.CharField(max_length=20, unique=True, verbose_name="Код")
    name = models.CharField(max_length=100, verbose_name="Наименование")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Вид брака"
        verbose_name_plural = "Виды брака"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class DefectReport(models.Model):
    """Акт о браке заготовок"""

    number = models.CharField(max_length=50, unique=True, verbose_name="Номер акта")
    production_site = models.ForeignKey(
        ProductionSite,
        on_delete=models.PROTECT,
        related_name="defect_reports",
        verbose_name="Участок",
    )
    blank = models.ForeignKey(
        "blanks.Blank", on_delete=models.PROTECT, verbose_name="Заготовка"
    )
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Количество бракованных"
    )
    defect_type = models.ForeignKey(
        DefectType, on_delete=models.PROTECT, verbose_name="Вид брака"
    )

    report_date = models.DateField(default=timezone.now, verbose_name="Дата акта")
    detected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="detected_defects",
        verbose_name="Обнаружил",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="confirmed_defects",
        verbose_name="Подтвердил",
    )

    description = models.TextField(verbose_name="Описание брака")
    photo = models.ImageField(
        upload_to="defects/", blank=True, null=True, verbose_name="Фото брака"
    )

    is_confirmed = models.BooleanField(default=False, verbose_name="Подтвержден")
    confirmed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата подтверждения"
    )

    is_written_off = models.BooleanField(
        default=False, verbose_name="Заготовки списаны"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Акт о браке"
        verbose_name_plural = "Акты о браке"
        ordering = ["-report_date"]

    def __str__(self):
        return f"{self.number} - {self.blank.name}: {self.quantity}"

    def save(self, *args, **kwargs):

        if not self.number:
            last_today = DefectReport.objects.filter(
                report_date=self.report_date
            ).count()
            self.number = (
                f"DF-{self.report_date.strftime('%Y%m%d')}-{last_today + 1:04d}"
            )

        is_new = not self.pk
        old_instance = None

        if not is_new:
            try:
                old_instance = DefectReport.objects.get(pk=self.pk)
            except DefectReport.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        should_write_off = (
            self.is_confirmed
            and not self.is_written_off
            and (is_new or (old_instance and not old_instance.is_confirmed))
        )

        if should_write_off:
            self.write_off_blanks()

            self.is_written_off = True

            super().save(update_fields=["is_written_off"])

    def write_off_blanks(self):
        """Списание бракованных заготовок с участка"""
        try:
            balance = SiteBalance.objects.get(
                production_site=self.production_site, blank=self.blank
            )

            if balance.quantity < self.quantity:
                print(
                    f"ВНИМАНИЕ: На участке {self.production_site.code} недостаточно заготовок "
                    f"{self.blank.name}. Требуется: {self.quantity}, в наличии: {balance.quantity}"
                )

            balance.quantity -= self.quantity
            balance.save()

            from warehouse.models import StockMovement

            StockMovement.objects.create(
                movement_type="write_off",
                from_warehouse=self.production_site.warehouse,
                blank=self.blank,
                quantity=self.quantity,
                movement_date=timezone.now(),
                reason=f"Брак по акту {self.number}",
                created_by=self.confirmed_by or self.detected_by,
            )

            print(
                f"Списано {self.quantity} {self.blank.unit} {self.blank.name} "
                f"с участка {self.production_site.code}"
            )

        except SiteBalance.DoesNotExist:
            print(
                f"ОШИБКА: На участке {self.production_site.code} нет остатков заготовки {self.blank.name}"
            )

            from warehouse.models import StockMovement

            StockMovement.objects.create(
                movement_type="write_off",
                from_warehouse=self.production_site.warehouse,
                blank=self.blank,
                quantity=self.quantity,
                movement_date=timezone.now(),
                reason=f"Брак по акту {self.number} (списание при отсутствии остатков)",
                created_by=self.confirmed_by or self.detected_by,
            )


class QualityStandard(models.Model):
    """Стандарты качества для изделий"""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="quality_standards",
        verbose_name="Изделие",
    )
    name = models.CharField(max_length=100, verbose_name="Название стандарта")
    description = models.TextField(verbose_name="Описание")
    document = models.FileField(
        upload_to="quality/standards/", blank=True, null=True, verbose_name="Документ"
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Стандарт качества"
        verbose_name_plural = "Стандарты качества"
        ordering = ["product", "name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"
