from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .forms import ProductForm, ConsumptionNormForm
from .models import Product, ProductCategory, ConsumptionNorm
from blanks.models import Blank, BlankCategory

User = get_user_model()


class ProductModelTest(TestCase):
    """Тесты модели изделия"""

    def setUp(self):
        self.category = ProductCategory.objects.create(name="Задвижки клиновые")
        self.product = Product.objects.create(
            article="30с41нж-50",
            name="задвижка 30с41нж Ру 16 Ду 50",
            category=self.category,
            description="Тестовое описание",
        )

    def test_create_product(self):
        """Тест создания изделия"""
        self.assertEqual(self.product.article, "30с41нж-50")
        self.assertEqual(self.product.name, "задвижка 30с41нж Ру 16 Ду 50")
        self.assertEqual(self.product.category.name, "Задвижки клиновые")
        self.assertTrue(self.product.is_active)

    def test_product_str(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.product), "30с41нж-50 - задвижка 30с41нж Ру 16 Ду 50")


class ConsumptionNormModelTest(TestCase):
    """Тесты норм расхода"""

    def setUp(self):
        self.prod_category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="задвижка 50", category=self.prod_category
        )
        self.blank_category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка 50-16", category=self.blank_category, unit="шт"
        )
        self.norm = ConsumptionNorm.objects.create(
            product=self.product, blank=self.blank, quantity=2
        )

    def test_create_norm(self):
        """Тест создания нормы"""
        self.assertEqual(self.norm.product, self.product)
        self.assertEqual(self.norm.blank, self.blank)
        self.assertEqual(self.norm.quantity, 2)

    def test_unique_norm(self):
        """Тест уникальности нормы"""
        with self.assertRaises(Exception):
            ConsumptionNorm.objects.create(
                product=self.product, blank=self.blank, quantity=3
            )


class ProductViewsTest(TestCase):
    """Тесты представлений изделий"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="technologist@test.ru",
            password="testpass123",
            role="technologist",
            is_approved=True,
        )
        self.category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="задвижка 50", category=self.category
        )

    def test_product_list_view(self):
        """Тест списка изделий"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")

    def test_product_detail_view(self):
        """Тест детальной страницы изделия"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.get(
            reverse("products:product_detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_detail.html")


class ProductFormTest(TestCase):
    """Тесты формы изделия"""

    def setUp(self):
        self.category = ProductCategory.objects.create(name="Задвижки")
        self.valid_data = {
            "article": "30с41нж-50",
            "name": "Задвижка 50",
            "category": self.category.pk,
            "description": "Тестовое описание",
            "is_active": True,
        }

    def test_valid_form(self):
        """Тест валидной формы"""
        form = ProductForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_without_article(self):
        """Тест невалидной формы без артикула"""
        data = self.valid_data.copy()
        data.pop("article")
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("article", form.errors)


class ConsumptionNormFormTest(TestCase):
    """Тесты формы норм расхода"""

    def setUp(self):
        self.category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="Задвижка 50", category=self.category
        )
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")

    def test_valid_form(self):
        """Тест валидной формы"""
        form = ConsumptionNormForm(
            data={
                "product": self.product.pk,
                "blank": self.blank.pk,
                "quantity": 2,
            }
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_norm(self):
        """Тест на дубликат нормы"""
        ConsumptionNorm.objects.create(
            product=self.product, blank=self.blank, quantity=1
        )
        form = ConsumptionNormForm(
            data={
                "product": self.product.pk,
                "blank": self.blank.pk,
                "quantity": 2,
            }
        )
        self.assertFalse(form.is_valid())


class ConsumptionNormViewTest(TestCase):
    """Тесты представлений норм расхода"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="technologist@test.ru",
            password="tech123",
            role="technologist",
            is_approved=True,
        )
        self.category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="Задвижка 50", category=self.category
        )
        self.blank = Blank.objects.create(article="0909", name="крышка", unit="шт")
        self.norm = ConsumptionNorm.objects.create(
            product=self.product, blank=self.blank, quantity=2
        )

    def test_norm_list_view(self):
        """Тест списка норм"""
        self.client.login(username="technologist@test.ru", password="tech123")
        response = self.client.get(reverse("products:norm_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/norm_list.html")

    def test_norm_detail_view(self):
        """Тест детальной страницы нормы"""
        self.client.login(username="technologist@test.ru", password="tech123")
        response = self.client.get(reverse("products:norm_detail", args=[self.norm.pk]))
        self.assertEqual(response.status_code, 200)

    def test_norm_delete_view(self):
        """Тест удаления нормы"""
        self.client.login(username="technologist@test.ru", password="tech123")
        response = self.client.post(
            reverse("products:norm_delete", args=[self.norm.pk])
        )
        self.assertRedirects(response, reverse("products:norm_list"))
        self.assertEqual(ConsumptionNorm.objects.count(), 0)


class ProductDeleteViewTest(TestCase):
    """Тест удаления изделия"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
        )
        self.category = ProductCategory.objects.create(name="Задвижки")
        self.product = Product.objects.create(
            article="30с41нж-50", name="Задвижка 50", category=self.category
        )

    def test_product_delete_view(self):
        """Тест удаления изделия"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(
            reverse("products:product_delete", args=[self.product.pk])
        )
        self.assertRedirects(response, reverse("products:product_list"))
        self.assertEqual(Product.objects.count(), 0)
