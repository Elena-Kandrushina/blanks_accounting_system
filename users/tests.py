from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.forms import UserCreationForm

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты модели пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
        )

    def test_create_user(self):
        """Тест создания обычного пользователя"""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpass123"))
        self.assertEqual(self.user.role, "technologist")
        self.assertFalse(self.user.is_approved)
        self.assertFalse(self.user.is_superuser)

    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            first_name="Админ",
            last_name="Админов",
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, "admin")

    def test_user_str(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.user), "test@example.com (Технолог)")

    def test_role_properties(self):
        """Тест свойств ролей"""
        self.assertTrue(self.user.is_technologist)
        self.assertFalse(self.user.is_storekeeper)
        self.assertFalse(self.user.is_production_master)
        self.assertFalse(self.user.is_administrator)


class UserAuthenticationTest(TestCase):
    """Тесты аутентификации"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
            is_approved=True,
        )

    def test_login_view(self):
        """Тест страницы входа"""
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_successful_login(self):
        """Тест успешного входа"""
        response = self.client.post(
            reverse("users:login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertRedirects(response, reverse("users:technologist_dashboard"))

    def test_failed_login(self):
        """Тест неудачного входа"""
        response = self.client.post(
            reverse("users:login"),
            {"username": "test@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Please enter a correct")

    def test_logout(self):
        """Тест выхода"""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.post(reverse("users:logout"))
        self.assertRedirects(response, reverse("users:login"))


class UserRegistrationTest(TestCase):
    """Тесты регистрации"""

    def test_register_view(self):
        """Тест страницы регистрации"""
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_successful_registration(self):
        """Тест успешной регистрации"""
        response = self.client.post(
            reverse("users:register"),
            {
                "email": "new@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "role": "storekeeper",
                "password1": "testpass123",
                "password2": "testpass123",
            },
        )
        self.assertRedirects(response, reverse("users:login"))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.email, "new@example.com")
        self.assertFalse(user.is_approved)
        self.assertFalse(user.is_active)


class UserDashboardRedirectTest(TestCase):
    """Тесты перенаправления на дашборды"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
            is_approved=True,
        )

    def test_dashboard_redirect(self):
        """Тест перенаправления на дашборд"""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(reverse("users:dashboard_redirect"))
        self.assertRedirects(response, reverse("users:technologist_dashboard"))


class UserPermissionsTest(TestCase):
    """Тесты прав доступа"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
            is_superuser=True,
        )
        self.technologist = User.objects.create_user(
            email="technologist@test.ru",
            password="tech123",
            role="technologist",
            is_approved=True,
        )
        self.storekeeper = User.objects.create_user(
            email="storekeeper@test.ru",
            password="store123",
            role="storekeeper",
            is_approved=True,
        )
        self.master = User.objects.create_user(
            email="master@test.ru",
            password="master123",
            role="production_master",
            is_approved=True,
        )
        self.otk = User.objects.create_user(
            email="otk@test.ru",
            password="otk123",
            role="otk_senior",
            is_approved=True,
        )
        self.regular_user = User.objects.create_user(
            email="user@test.ru",
            password="user123",
            role="technologist",
            is_approved=True,
        )

    def test_admin_can_access_admin_pages(self):
        """Админ имеет доступ к админским страницам"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_technologist_cannot_access_admin_pages(self):
        """Технолог не имеет доступа к админским страницам"""
        self.client.login(username="technologist@test.ru", password="tech123")
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_storekeeper_cannot_access_admin_pages(self):
        """Кладовщик не имеет доступа к админским страницам"""
        self.client.login(username="storekeeper@test.ru", password="store123")
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, 403)


class ProfileViewTest(TestCase):
    """Тесты профиля пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
            is_approved=True,
        )

    def test_profile_view(self):
        """Тест страницы профиля"""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertContains(response, "Тест")
        self.assertContains(response, "Тестов")

    def test_profile_update(self):
        """Тест обновления профиля"""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.post(
            reverse("users:profile"),
            {
                "first_name": "НовоеИмя",
                "last_name": "НоваяФамилия",
                "phone_number": "123-45-67",
            },
        )
        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "НовоеИмя")
        self.assertEqual(self.user.last_name, "НоваяФамилия")
        self.assertEqual(self.user.phone_number, "123-45-67")


class PasswordChangeTest(TestCase):
    """Тесты смены пароля"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="oldpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
            is_approved=True,
        )

    def test_password_change_view(self):
        """Тест страницы смены пароля"""
        self.client.login(username="test@example.com", password="oldpass123")
        response = self.client.get(reverse("users:change_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/change_password.html")

    def test_successful_password_change(self):
        """Тест успешной смены пароля"""
        self.client.login(username="test@example.com", password="oldpass123")
        response = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": "oldpass123",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        self.assertRedirects(response, reverse("users:profile"))

        self.client.logout()
        login_successful = self.client.login(
            username="test@example.com", password="newpass123"
        )
        self.assertTrue(login_successful)

    def test_password_change_with_wrong_old_password(self):
        """Тест смены пароля с неверным старым паролем"""
        self.client.login(username="test@example.com", password="oldpass123")
        response = self.client.post(
            reverse("users:change_password"),
            {
                "old_password": "wrongpass",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly")


class UserAdminViewsTest(TestCase):
    """Тесты управления пользователями для администратора"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
            is_superuser=True,
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Тест",
            last_name="Тестов",
            role="technologist",
            is_approved=False,
        )

    def test_user_list_view(self):
        """Тест списка пользователей"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_list.html")
        self.assertContains(response, "test@example.com")

    def test_user_detail_view(self):
        """Тест детальной страницы пользователя"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_detail", args=[self.user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_detail.html")
        self.assertContains(response, "test@example.com")


class UserDeleteTest(TestCase):
    """Тесты удаления пользователя"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
            is_superuser=True,
        )
        self.user_to_delete = User.objects.create_user(
            email="delete@example.com",
            password="delete123",
            first_name="Удаляемый",
            last_name="Пользователь",
            role="technologist",
        )

    def test_user_delete_view(self):
        """Тест удаления пользователя"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(
            reverse("users:user_delete", args=[self.user_to_delete.pk])
        )
        self.assertRedirects(response, reverse("users:user_list"))

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=self.user_to_delete.pk)

    def test_cannot_delete_self(self):
        """Тест запрета удаления самого себя"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.post(reverse("users:user_delete", args=[self.admin.pk]))
        self.assertRedirects(response, reverse("users:user_list"))

        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())


class UserListFilterTest(TestCase):
    """Тесты фильтрации списка пользователей"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
            is_superuser=True,
        )

        User.objects.create_user(
            email="tech@example.com",
            password="pass123",
            role="technologist",
            is_approved=True,
            department="Техотдел",
        )
        User.objects.create_user(
            email="store@example.com",
            password="pass123",
            role="storekeeper",
            is_approved=True,
            department="Склад",
        )
        User.objects.create_user(
            email="pending@example.com",
            password="pass123",
            role="production_master",
            is_approved=False,
            department="Участок",
        )

    def test_filter_by_role(self):
        """Тест фильтрации по роли"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_list"), {"role": "technologist"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tech@example.com")
        self.assertNotContains(response, "store@example.com")

    def test_filter_by_approval_status(self):
        """Тест фильтрации по статусу подтверждения"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_list"), {"approved": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pending@example.com")
        self.assertNotContains(response, "tech@example.com")

    def test_search_users(self):
        """Тест поиска пользователей"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:user_list"), {"search": "tech"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tech@example.com")
        self.assertNotContains(response, "store@example.com")


class DashboardViewsTest(TestCase):
    """Тесты дашбордов"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.ru",
            password="admin123",
            role="admin",
            is_approved=True,
        )
        self.technologist = User.objects.create_user(
            email="tech@test.ru",
            password="tech123",
            role="technologist",
            is_approved=True,
        )

    def test_admin_dashboard(self):
        """Тест дашборда администратора"""
        self.client.login(username="admin@test.ru", password="admin123")
        response = self.client.get(reverse("users:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/dashboards/simple_dashboard.html")
        self.assertContains(response, "Управление пользователями")

    def test_technologist_dashboard(self):
        """Тест дашборда технолога"""
        self.client.login(username="tech@test.ru", password="tech123")
        response = self.client.get(reverse("users:technologist_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Создать заготовку")

    def test_technologist_cannot_access_admin_dashboard(self):
        """Технолог не может зайти в дашборд админа"""
        self.client.login(username="tech@test.ru", password="tech123")
        response = self.client.get(reverse("users:admin_dashboard"))
        self.assertEqual(response.status_code, 403)


class HomeViewTest(TestCase):
    """Тесты домашней страницы"""

    def test_home_view_unauthenticated(self):
        """Домашняя страница для неавторизованного пользователя"""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "Войти")
        self.assertContains(response, "Регистрация")

    def test_home_view_authenticated_redirects_to_dashboard(self):
        """Авторизованный пользователь перенаправляется на дашборд"""
        User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role="technologist",
            is_approved=True,
        )
        self.client.login(username="test@example.com", password="testpass123")

        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response, reverse("users:dashboard_redirect"), fetch_redirect_response=False
        )


class UserCreationFormTest(TestCase):
    """Тесты формы регистрации"""

    def test_password_mismatch(self):
        """Тест на несовпадение паролей"""
        form = UserCreationForm(
            data={
                "email": "test@example.com",
                "first_name": "Тест",
                "last_name": "Тестов",
                "role": "technologist",
                "password1": "pass123",
                "password2": "pass456",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_email(self):
        """Тест на дубликат email"""
        User.objects.create_user(
            email="test@example.com",
            password="pass123",
            first_name="Существующий",
            last_name="Пользователь",
        )
        form = UserCreationForm(
            data={
                "email": "test@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "role": "technologist",
                "password1": "pass123",
                "password2": "pass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
