from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .forms import AssemblyReportForm, BlankReceiptForm, ProductionSiteForm
from .models import ProductionSite, BlankReceipt, AssemblyReport, SiteBalance
from blanks.models import Blank, BlankCategory
from products.models import Product, ProductCategory, ConsumptionNorm
from warehouse.models import Warehouse, StockBalance

User = get_user_model()


class ProductionSiteModelTest(TestCase):
    """Тесты модели производственного участка"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.site = ProductionSite.objects.create(
            code="УЧ-01", name="Участок 1", warehouse=self.warehouse
        )

    def test_create_site(self):
        """Тест создания участка"""
        self.assertEqual(self.site.code, "УЧ-01")
        self.assertEqual(self.site.name, "Участок 1")
        self.assertEqual(self.site.warehouse, self.warehouse)
        self.assertTrue(self.site.is_active)


class BlankReceiptModelTest(TestCase):
    """Тесты заявок на выдачу"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="master@test.ru", password="testpass123", role="production_master"
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.site = ProductionSite.objects.create(
            code="УЧ-01", name="Участок", warehouse=self.warehouse
        )
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.receipt = BlankReceipt.objects.create(
            production_site=self.site,
            blank=self.blank,
            quantity=50,
            created_by=self.user,
            status="new",
        )

    def test_create_receipt(self):
        """Тест создания заявки"""
        self.assertEqual(self.receipt.production_site, self.site)
        self.assertEqual(self.receipt.blank, self.blank)
        self.assertEqual(self.receipt.quantity, 50)
        self.assertEqual(self.receipt.status, "new")
        self.assertIsNotNone(self.receipt.number)

    def test_receipt_number_generation(self):
        """Тест генерации номера заявки"""
        self.assertTrue(self.receipt.number.startswith("REQ-"))


class AssemblyReportModelTest(TestCase):
    """Тесты отчетов о сборке"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="worker@test.ru", password="testpass123", role="production_master"
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.site = ProductionSite.objects.create(
            code="УЧ-01", name="Участок", warehouse=self.warehouse
        )
        self.prod_category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="задвижка", category=self.prod_category
        )
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        ConsumptionNorm.objects.create(
            product=self.product, blank=self.blank, quantity=1
        )

        SiteBalance.objects.create(
            production_site=self.site, blank=self.blank, quantity=100
        )
        self.report = AssemblyReport.objects.create(
            product=self.product,
            production_site=self.site,
            quantity=10,
            produced_by=self.user,
        )

    def test_create_report(self):
        """Тест создания отчета"""
        self.assertEqual(self.report.product, self.product)
        self.assertEqual(self.report.production_site, self.site)
        self.assertEqual(self.report.quantity, 10)
        self.assertIsNotNone(self.report.number)
        self.assertTrue(self.report.number.startswith("AR-"))

    def test_report_consumes_blanks(self):
        """Тест списания заготовок при создании отчета"""
        balance = SiteBalance.objects.get(production_site=self.site, blank=self.blank)
        self.assertEqual(balance.quantity, 90)  # 100 - 10


class ProductionViewsTest(TestCase):
    """Тесты представлений производства"""

    def setUp(self):
        self.master = User.objects.create_user(
            email="master@test.ru",
            password="testpass123",
            role="production_master",
            is_approved=True,
        )
        self.storekeeper = User.objects.create_user(
            email="storekeeper@test.ru",
            password="testpass123",
            role="storekeeper",
            is_approved=True,
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.site = ProductionSite.objects.create(
            code="УЧ-01", name="Участок", warehouse=self.warehouse
        )
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )

        StockBalance.objects.create(
            warehouse=self.warehouse, blank=self.blank, quantity=200
        )

    def test_receipt_create_view_master(self):
        """Тест создания заявки мастером"""
        self.client.login(username="master@test.ru", password="testpass123")
        response = self.client.post(
            reverse("production:receipt_create"),
            {
                "production_site": self.site.pk,
                "blank": self.blank.pk,
                "quantity": 50,
                "receipt_date": timezone.now(),
            },
        )
        self.assertRedirects(response, reverse("production:receipt_list"))
        self.assertEqual(BlankReceipt.objects.count(), 1)

    def test_receipt_process_view_storekeeper(self):
        """Тест обработки заявки кладовщиком"""
        receipt = BlankReceipt.objects.create(
            production_site=self.site,
            blank=self.blank,
            quantity=50,
            created_by=self.master,
            status="new",
        )
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.post(
            reverse("production:receipt_process", args=[receipt.pk])
        )
        self.assertRedirects(response, reverse("production:storekeeper_receipt_list"))
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, "completed")


class ProductionSiteFormTest(TestCase):
    """Тесты формы участка"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")

    def test_valid_form(self):
        """Тест валидной формы"""
        form = ProductionSiteForm(
            data={
                "code": "УЧ-03",
                "name": "Новый участок",
                "warehouse": self.warehouse.pk,
            }
        )
        self.assertTrue(form.is_valid())


class BlankReceiptFormTest(TestCase):
    """Тесты формы заявки"""

    def setUp(self):
        self.site = ProductionSite.objects.create(code="УЧ-01", name="Участок")
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")

    def test_valid_form(self):
        """Тест валидной формы"""
        form = BlankReceiptForm(
            data={
                "production_site": self.site.pk,
                "blank": self.blank.pk,
                "quantity": 50,
                "receipt_date": timezone.now(),
            }
        )
        self.assertTrue(form.is_valid())

    def test_negative_quantity(self):
        """Тест на отрицательное количество"""
        form = BlankReceiptForm(
            data={
                "production_site": self.site.pk,
                "blank": self.blank.pk,
                "quantity": -10,
                "receipt_date": timezone.now(),
            }
        )
        self.assertFalse(form.is_valid())


class AssemblyReportFormTest(TestCase):
    """Тесты формы отчета о сборке"""

    def setUp(self):

        self.category = ProductCategory.objects.create(name="Задвижки")

        self.product = Product.objects.create(
            article="30с41нж-50", name="Задвижка 50", category=self.category
        )
        self.site = ProductionSite.objects.create(code="УЧ-01", name="Участок")
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")
        ConsumptionNorm.objects.create(
            product=self.product, blank=self.blank, quantity=2
        )
        SiteBalance.objects.create(
            production_site=self.site, blank=self.blank, quantity=100
        )

    def test_valid_form(self):
        """Тест валидной формы"""
        form = AssemblyReportForm(
            data={
                "product": self.product.pk,
                "production_site": self.site.pk,
                "quantity": 10,
                "defect_quantity": 0,
                "report_date": timezone.now().date(),
            }
        )

        self.assertTrue(form.is_valid())

    def test_insufficient_stock(self):
        """Тест на недостаток заготовок"""
        form = AssemblyReportForm(
            data={
                "product": self.product.pk,
                "production_site": self.site.pk,
                "quantity": 1000,
                "report_date": timezone.now().date(),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Недостаточно заготовок", str(form.errors))


class ProductionSiteViewTest(TestCase):
    """Тесты представлений участков"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru", password="admin123", role="admin", is_approved=True
        )
        self.site = ProductionSite.objects.create(code="УЧ-01", name="Участок 1")

    def test_site_create_view(self):
        """Тест создания участка"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(
            reverse("production:site_create"),
            {"code": "УЧ-03", "name": "Новый участок"},
        )
        self.assertRedirects(response, reverse("production:site_list"))
        self.assertEqual(ProductionSite.objects.count(), 2)

    def test_site_update_view(self):
        """Тест редактирования участка"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(
            reverse("production:site_edit", args=[self.site.pk]),
            {"code": "УЧ-01", "name": "Измененное название"},
        )
        self.assertRedirects(
            response, reverse("production:site_detail", args=[self.site.pk])
        )
        self.site.refresh_from_db()
        self.assertEqual(self.site.name, "Измененное название")

    def test_site_delete_view(self):
        """Тест удаления участка"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(
            reverse("production:site_delete", args=[self.site.pk])
        )
        self.assertRedirects(response, reverse("production:site_list"))
        self.assertEqual(ProductionSite.objects.count(), 0)


class BlankReceiptCancelViewTest(TestCase):
    """Тест отмены заявки"""

    def setUp(self):
        self.master = User.objects.create_user(
            email="master@test.ru",
            password="master123",
            role="production_master",
            is_approved=True,
        )
        self.site = ProductionSite.objects.create(code="УЧ-01", name="Участок")
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")
        self.receipt = BlankReceipt.objects.create(
            production_site=self.site,
            blank=self.blank,
            quantity=50,
            created_by=self.master,
            status="new",
        )

    def test_cancel_receipt(self):
        """Тест отмены заявки"""
        self.client.login(username="master@test.ru", password="master123")
        response = self.client.post(
            reverse("production:receipt_cancel", args=[self.receipt.pk]),
            {"reason": "Передумали"},
        )
        self.assertRedirects(response, reverse("production:receipt_list"))
        self.receipt.refresh_from_db()
        self.assertEqual(self.receipt.status, "cancelled")
