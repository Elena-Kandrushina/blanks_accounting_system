from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import DefectType, DefectReport
from blanks.models import Blank, BlankCategory
from production.models import ProductionSite, SiteBalance
from warehouse.models import Warehouse

User = get_user_model()


class DefectTypeModelTest(TestCase):
    """Тесты модели вида брака"""

    def setUp(self):
        self.defect_type = DefectType.objects.create(
            code="ТРЕЩ", name="Трещина", description="Трещина в материале"
        )

    def test_create_defect_type(self):
        """Тест создания вида брака"""
        self.assertEqual(self.defect_type.code, "ТРЕЩ")
        self.assertEqual(self.defect_type.name, "Трещина")
        self.assertTrue(self.defect_type.is_active)


class DefectReportModelTest(TestCase):
    """Тесты акта о браке"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="otk@test.ru", password="testpass123", role="otk_senior"
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.site = ProductionSite.objects.create(
            code="УЧ-01", name="Участок", warehouse=self.warehouse
        )
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.defect_type = DefectType.objects.create(code="ТРЕЩ", name="Трещина")

        SiteBalance.objects.create(
            production_site=self.site, blank=self.blank, quantity=100
        )
        self.report = DefectReport.objects.create(
            production_site=self.site,
            blank=self.blank,
            quantity=5,
            defect_type=self.defect_type,
            description="Трещина на корпусе",
            detected_by=self.user,
            is_confirmed=False,
        )

    def test_create_report(self):
        """Тест создания акта"""
        self.assertEqual(self.report.production_site, self.site)
        self.assertEqual(self.report.blank, self.blank)
        self.assertEqual(self.report.quantity, 5)
        self.assertEqual(self.report.defect_type, self.defect_type)
        self.assertFalse(self.report.is_confirmed)
        self.assertIsNotNone(self.report.number)
        self.assertTrue(self.report.number.startswith("DF-"))

    def test_confirm_report_consumes_blanks(self):
        """Тест списания заготовок при подтверждении акта"""
        balance_before = SiteBalance.objects.get(
            production_site=self.site, blank=self.blank
        ).quantity

        self.report.is_confirmed = True
        self.report.confirmed_by = self.user
        self.report.confirmed_at = timezone.now()
        self.report.save()

        balance_after = SiteBalance.objects.get(
            production_site=self.site, blank=self.blank
        ).quantity

        self.assertEqual(balance_after, balance_before - 5)


class QualityControlViewsTest(TestCase):
    """Тесты представлений ОТК"""

    def setUp(self):
        self.otk_user = User.objects.create_user(
            email="otk@test.ru",
            password="testpass123",
            role="otk_senior",
            is_approved=True,
        )
        self.regular_user = User.objects.create_user(
            email="user@test.ru",
            password="testpass123",
            role="technologist",
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
        self.defect_type = DefectType.objects.create(code="ТРЕЩ", name="Трещина")

    def test_defect_report_list_view_otk(self):
        """Тест доступа к списку актов для ОТК"""
        self.client.login(username="otk@test.ru", password="testpass123")
        response = self.client.get(reverse("quality_control:defectreport_list"))
        self.assertEqual(response.status_code, 200)

    def test_defect_report_list_view_regular_user(self):
        """Тест доступа к списку актов для обычного пользователя"""
        self.client.login(username="user@test.ru", password="testpass123")
        response = self.client.get(reverse("quality_control:defectreport_list"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_defect_report_create_view(self):
        """Тест создания акта"""
        self.client.login(username="otk@test.ru", password="testpass123")
        response = self.client.post(
            reverse("quality_control:defectreport_create"),
            {
                "production_site": self.site.pk,
                "blank": self.blank.pk,
                "quantity": 3,
                "defect_type": self.defect_type.pk,
                "description": "Тестовый брак",
            },
        )
        self.assertRedirects(response, reverse("quality_control:defectreport_list"))
        self.assertEqual(DefectReport.objects.count(), 1)


class DefectReportConfirmTest(TestCase):
    """Тесты подтверждения акта о браке"""

    def setUp(self):
        self.otk = User.objects.create_user(
            email="otk@test.ru",
            password="otk123",
            role="otk_senior",
            is_approved=True,
        )
        self.site = ProductionSite.objects.create(code="УЧ-01", name="Участок")
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")
        self.defect_type = DefectType.objects.create(code="ТРЕЩ", name="Трещина")
        SiteBalance.objects.create(
            production_site=self.site, blank=self.blank, quantity=100
        )
        self.report = DefectReport.objects.create(
            production_site=self.site,
            blank=self.blank,
            quantity=5,
            defect_type=self.defect_type,
            description="Брак",
            detected_by=self.otk,
            is_confirmed=False,
        )

    def test_confirm_report_view(self):
        """Тест подтверждения акта"""
        self.client.login(username="otk@test.ru", password="otk123")
        response = self.client.post(
            reverse("quality_control:defectreport_confirm", args=[self.report.pk])
        )
        self.assertRedirects(
            response,
            reverse("quality_control:defectreport_detail", args=[self.report.pk]),
        )
        self.report.refresh_from_db()
        self.assertTrue(self.report.is_confirmed)
        self.assertIsNotNone(self.report.confirmed_at)

        balance = SiteBalance.objects.get(production_site=self.site, blank=self.blank)
        self.assertEqual(balance.quantity, 95)
