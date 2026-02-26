from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Blank, BlankCategory

User = get_user_model()


class BlankModelTest(TestCase):
    """Тесты модели заготовки"""

    def setUp(self):
        self.category = BlankCategory.objects.create(
            name="Крышки", description="Крышки для задвижек"
        )
        self.blank = Blank.objects.create(
            article="0909",
            name="крышка 50-16",
            category=self.category,
            unit="шт",
            weight=2.5,
        )

    def test_create_blank(self):
        """Тест создания заготовки"""
        self.assertEqual(self.blank.article, "0909")
        self.assertEqual(self.blank.name, "крышка 50-16")
        self.assertEqual(self.blank.category.name, "Крышки")
        self.assertEqual(self.blank.unit, "шт")
        self.assertEqual(self.blank.weight, 2.5)
        self.assertTrue(self.blank.is_active)

    def test_blank_str(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.blank), "0909 - крышка 50-16")

    def test_unique_article(self):
        """Тест уникальности артикула"""
        with self.assertRaises(Exception):
            Blank.objects.create(
                article="0909", name="другая крышка", category=self.category, unit="шт"
            )


class BlankViewsTest(TestCase):
    """Тесты представлений заготовок"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="technologist@test.ru",
            password="testpass123",
            role="technologist",
            is_approved=True,
        )
        self.category = BlankCategory.objects.create(name="Крышки")
        self.blank = Blank.objects.create(
            article="0909", name="крышка 50-16", category=self.category, unit="шт"
        )

    def test_blank_list_view(self):
        """Тест списка заготовок"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.get(reverse("blanks:blank_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blanks/blank_list.html")
        self.assertContains(response, "0909")

    def test_blank_detail_view(self):
        """Тест детальной страницы заготовки"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.get(reverse("blanks:blank_detail", args=[self.blank.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blanks/blank_detail.html")
        self.assertContains(response, "крышка 50-16")

    def test_blank_create_view(self):
        """Тест создания заготовки"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.post(
            reverse("blanks:blank_create"),
            {
                "article": "1111",
                "name": "корпус 50-16",
                "category": self.category.pk,
                "unit": "шт",
                "weight": 5.2,
            },
        )
        self.assertRedirects(response, reverse("blanks:blank_list"))
        self.assertEqual(Blank.objects.count(), 2)

    def test_blank_edit_view(self):
        """Тест редактирования заготовки"""
        self.client.login(username="technologist@test.ru", password="testpass123")
        response = self.client.post(
            reverse("blanks:blank_edit", args=[self.blank.pk]),
            {
                "article": "0909",
                "name": "крышка 50-16 (новая)",
                "category": self.category.pk,
                "unit": "шт",
                "weight": 3.0,
            },
        )
        self.assertRedirects(
            response, reverse("blanks:blank_detail", args=[self.blank.pk])
        )
        self.blank.refresh_from_db()
        self.assertEqual(self.blank.name, "крышка 50-16 (новая)")
        self.assertEqual(self.blank.weight, 3.0)
