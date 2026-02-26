from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Warehouse, StockBalance, StockMovement
from blanks.models import Blank, BlankCategory
from django.utils import timezone

User = get_user_model()


class WarehouseModelTest(TestCase):
    """Тесты модели склада"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(
            code="СК-01", name="Склад заготовок", address="г. Москва, ул. Промышленная"
        )

    def test_create_warehouse(self):
        """Тест создания склада"""
        self.assertEqual(self.warehouse.code, "СК-01")
        self.assertEqual(self.warehouse.name, "Склад заготовок")
        self.assertTrue(self.warehouse.is_active)


class StockBalanceModelTest(TestCase):
    """Тесты остатков"""

    def setUp(self):
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.balance = StockBalance.objects.create(
            warehouse=self.warehouse, blank=self.blank, quantity=100, min_stock=20
        )

    def test_create_balance(self):
        """Тест создания остатка"""
        self.assertEqual(self.balance.warehouse, self.warehouse)
        self.assertEqual(self.balance.blank, self.blank)
        self.assertEqual(self.balance.quantity, 100)
        self.assertEqual(self.balance.min_stock, 20)


class StockMovementModelTest(TestCase):
    """Тесты движений"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="storekeeper@test.ru", password="testpass123", role="storekeeper"
        )
        self.warehouse1 = Warehouse.objects.create(code="СК-01", name="Склад 1")
        self.warehouse2 = Warehouse.objects.create(code="СК-02", name="Склад 2")
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.movement = StockMovement.objects.create(
            movement_type="transfer",
            from_warehouse=self.warehouse1,
            to_warehouse=self.warehouse2,
            blank=self.blank,
            quantity=50,
            movement_date=timezone.now(),
            created_by=self.user,
        )

    def test_create_movement(self):
        """Тест создания движения"""
        self.assertEqual(self.movement.movement_type, "transfer")
        self.assertEqual(self.movement.from_warehouse, self.warehouse1)
        self.assertEqual(self.movement.to_warehouse, self.warehouse2)
        self.assertEqual(self.movement.blank, self.blank)
        self.assertEqual(self.movement.quantity, 50)

    def test_movement_number_generation(self):
        """Тест генерации номера движения"""
        self.assertIsNotNone(self.movement.number)
        self.assertTrue(self.movement.number.startswith("MOV-"))


class WarehouseViewsTest(TestCase):
    """Тесты представлений склада"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="storekeeper@test.ru",
            password="testpass123",
            role="storekeeper",
            is_approved=True,
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )

    def test_warehouse_list_view(self):
        """Тест списка складов"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.get(reverse("warehouse:warehouse_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "warehouse/warehouse_list.html")

    def test_balance_list_view(self):
        """Тест списка остатков"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.get(reverse("warehouse:balance_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "warehouse/stockbalance_list.html")


class StockMovementViewsTest(TestCase):
    """Тесты представлений движений"""

    def setUp(self):
        self.storekeeper = User.objects.create_user(
            email="storekeeper@test.ru",
            password="testpass123",
            role="storekeeper",
            is_approved=True,
        )
        self.warehouse1 = Warehouse.objects.create(code="СК-01", name="Склад 1")
        self.warehouse2 = Warehouse.objects.create(code="СК-02", name="Склад 2")
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.balance = StockBalance.objects.create(
            warehouse=self.warehouse1, blank=self.blank, quantity=200, min_stock=30
        )

    def test_movement_list_view(self):
        """Тест списка движений"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.get(reverse("warehouse:movement_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "warehouse/stockmovement_list.html")

    def test_movement_create_view_receipt(self):
        """Тест создания поступления"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.post(
            reverse("warehouse:movement_create"),
            {
                "movement_type": "receipt",
                "to_warehouse": self.warehouse1.pk,
                "blank": self.blank.pk,
                "quantity": 50,
                "movement_date": timezone.now(),
            },
        )
        self.assertRedirects(response, reverse("warehouse:movement_list"))

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 250)

    def test_movement_create_view_transfer(self):
        """Тест создания перемещения между складами"""

        StockBalance.objects.create(
            warehouse=self.warehouse2, blank=self.blank, quantity=100, min_stock=30
        )

        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.post(
            reverse("warehouse:movement_create"),
            {
                "movement_type": "transfer",
                "from_warehouse": self.warehouse1.pk,
                "to_warehouse": self.warehouse2.pk,
                "blank": self.blank.pk,
                "quantity": 30,
                "movement_date": timezone.now(),
            },
        )
        self.assertRedirects(response, reverse("warehouse:movement_list"))

        balance1 = StockBalance.objects.get(warehouse=self.warehouse1, blank=self.blank)
        balance2 = StockBalance.objects.get(warehouse=self.warehouse2, blank=self.blank)
        self.assertEqual(balance1.quantity, 170)  # 200 - 30
        self.assertEqual(balance2.quantity, 130)  # 100 + 30

    def test_movement_create_view_write_off(self):
        """Тест создания списания"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")
        response = self.client.post(
            reverse("warehouse:movement_create"),
            {
                "movement_type": "write_off",
                "from_warehouse": self.warehouse1.pk,
                "blank": self.blank.pk,
                "quantity": 20,
                "movement_date": timezone.now(),
                "reason": "Списание по браку",
            },
        )
        self.assertRedirects(response, reverse("warehouse:movement_list"))

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 180)  # 200 - 20

    def test_movement_create_view_insufficient_stock(self):
        """Тест списания при недостаточном остатке"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")

        response = self.client.post(
            reverse("warehouse:movement_create"),
            {
                "movement_type": "write_off",
                "from_warehouse": self.warehouse1.pk,
                "blank": self.blank.pk,
                "quantity": 300,
                "movement_date": timezone.now(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Недостаточно заготовок")
        self.assertTrue(response.context["form"].errors)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, 200)

    def test_movement_list_filters(self):
        """Тест фильтров в списке движений"""

        movement = StockMovement.objects.create(
            movement_type="receipt",
            to_warehouse=self.warehouse1,
            blank=self.blank,
            quantity=50,
            movement_date=timezone.now(),
            created_by=self.storekeeper,
        )

        self.client.login(username="storekeeper@test.ru", password="testpass123")

        response = self.client.get(
            reverse("warehouse:movement_list"), {"type": "receipt"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, movement.number)

        today = timezone.now().date().strftime("%Y-%m-%d")
        response = self.client.get(
            reverse("warehouse:movement_list"), {"date_from": today}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, movement.number)


class StockBalanceUpdateViewTest(TestCase):
    """Тесты обновления остатка"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="storekeeper@test.ru",
            password="testpass123",
            role="storekeeper",
            is_approved=True,
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка", category=self.blank_category, unit="шт"
        )
        self.balance = StockBalance.objects.create(
            warehouse=self.warehouse, blank=self.blank, quantity=200, min_stock=30
        )

    def test_balance_update_view(self):
        """Тест обновления минимального запаса"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")

        response = self.client.post(
            reverse("warehouse:balance_edit", args=[self.balance.pk]),
            {
                "warehouse": self.warehouse.pk,
                "blank": self.blank.pk,
                "quantity": self.balance.quantity,
                "min_stock": 50,
            },
        )

        self.assertRedirects(response, reverse("warehouse:balance_list"))

        self.balance.refresh_from_db()
        self.assertEqual(self.balance.min_stock, 50)
        self.assertEqual(self.balance.quantity, 200)


class StockReportViewTest(TestCase):
    """Тесты отчета по движениям"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="storekeeper@test.ru",
            password="testpass123",
            role="storekeeper",
            is_approved=True,
        )
        self.warehouse = Warehouse.objects.create(code="СК-01", name="Склад")
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")

    def test_stock_report_with_filters(self):
        """Тест отчета с фильтрами"""
        self.client.login(username="storekeeper@test.ru", password="testpass123")

        StockMovement.objects.create(
            movement_type="receipt",
            to_warehouse=self.warehouse,
            blank=self.blank,
            quantity=100,
            movement_date=timezone.now(),
            created_by=self.user,
        )

        today = timezone.now().date().strftime("%Y-%m-%d")
        response = self.client.get(
            reverse("warehouse:stock_report"),
            {"date_from": today, "date_to": today},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100.00")
