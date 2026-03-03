from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DetailView,
    TemplateView,
    RedirectView,
    DeleteView,
)
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from .models import User
from .forms import (
    UserCreationForm,
    UserProfileForm,
    UserChangeForm,
)


class AdminRequiredMixin(UserPassesTestMixin):
    """Только для администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role == "admin" or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden("Доступ запрещен. Требуются права администратора.")


class TechnologistRequiredMixin(UserPassesTestMixin):
    """Только для технологов и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ["admin", "technologist"]
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden("Доступ запрещен. Требуются права технолога.")


class StorekeeperRequiredMixin(UserPassesTestMixin):
    """Только для кладовщиков и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ["admin", "storekeeper"]
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden("Доступ запрещен. Требуются права кладовщика.")


class ProductionRequiredMixin(UserPassesTestMixin):
    """Только для производства и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role
            in ["admin", "production_master", "production_worker"]
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden(
            "Доступ запрещен. Требуются права производственного персонала."
        )


class ProductionMasterRequiredMixin(UserPassesTestMixin):
    """Только для мастеров участка и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ["admin", "production_master"]
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden(
            "Доступ запрещен. Требуются права мастера участка."
        )


class OTKSeniorRequiredMixin(UserPassesTestMixin):
    """Только для старших контролеров ОТК и администраторов"""

    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ["admin", "otk_senior"]
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return HttpResponseForbidden(
            "Доступ запрещен. Требуются права старшего контролера ОТК."
        )


class HomeView(TemplateView):
    """Домашняя страница"""

    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("users:dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CustomLoginView(SuccessMessageMixin, LoginView):
    """Авторизация пользователя"""

    form_class = AuthenticationForm
    template_name = "users/login.html"
    success_message = "Добро пожаловать, %(username)s!"

    def get_success_url(self):
        user = self.request.user
        if user.role == "admin":
            return reverse_lazy("users:admin_dashboard")
        elif user.role == "technologist":
            return reverse_lazy("users:technologist_dashboard")
        elif user.role == "storekeeper":
            return reverse_lazy("users:storekeeper_dashboard")
        elif user.role == "production_master":
            return reverse_lazy("users:production_master_dashboard")
        elif user.role == "otk_senior":
            return reverse_lazy("users:otk_senior_dashboard")
        return reverse_lazy("home")

    def get_success_message(self, cleaned_data):
        user = self.request.user
        return f"Добро пожаловать, {user.get_full_name() or user.email}!"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)


class CustomLogoutView(LogoutView):
    """Выход из системы"""

    next_page = reverse_lazy("users:login")

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Вы вышли из системы.")
        return super().dispatch(request, *args, **kwargs)


class RegisterView(SuccessMessageMixin, CreateView):
    """Регистрация нового пользователя"""

    model = User
    form_class = UserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")
    success_message = "Регистрация успешна! После подтверждения администратором вы сможете войти в систему."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("users:dashboard_redirect")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.is_active = False
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Просмотр и редактирование профиля"""

    model = User
    form_class = UserProfileForm
    template_name = "users/profile.html"
    success_message = "Профиль успешно обновлен!"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy("users:profile")


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление пользователя"""

    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("users:user_list")
    context_object_name = "user_obj"

    def dispatch(self, request, *args, **kwargs):

        obj = self.get_object()
        if obj.pk == request.user.pk:
            messages.error(request, "Вы не можете удалить自己的 учетную запись")
            return redirect("users:user_list")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(request, f"Пользователь {user.email} успешно удален")
        return super().delete(request, *args, **kwargs)


class CustomPasswordChangeView(
    LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView
):
    """Смена пароля"""

    form_class = PasswordChangeForm
    template_name = "users/change_password.html"
    success_url = reverse_lazy("users:profile")
    success_message = "Пароль успешно изменен!"


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Список пользователей (только для администраторов)"""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(department__icontains=search_query)
            )

        role_filter = self.request.GET.get("role", "")
        if role_filter:
            queryset = queryset.filter(role=role_filter)

        approved_filter = self.request.GET.get("approved", "")
        if approved_filter:
            is_approved = approved_filter == "approved"
            queryset = queryset.filter(is_approved=is_approved)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_choices"] = User.ROLE_CHOICES
        context["current_filters"] = {
            "search": self.request.GET.get("search", ""),
            "role": self.request.GET.get("role", ""),
            "approved": self.request.GET.get("approved", ""),
        }
        return context


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Детальная информация о пользователе"""

    model = User
    template_name = "users/user_detail.html"
    context_object_name = "user_obj"


class UserUpdateView(
    LoginRequiredMixin, AdminRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Редактирование пользователя администратором"""

    model = User
    form_class = UserChangeForm
    template_name = "users/user_form.html"

    def get_success_url(self):
        return reverse_lazy("users:user_detail", kwargs={"pk": self.object.pk})

    def get_success_message(self, cleaned_data):
        return f"Пользователь {self.object.email} успешно обновлен."


class ApproveUserView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Подтверждение пользователя"""

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs["pk"])
            user.is_approved = True
            user.is_active = True
            user.save()
            messages.success(request, f"Пользователь {user.email} подтвержден.")
        except User.DoesNotExist:
            messages.error(request, "Пользователь не найден.")

        return redirect("users:user_list")

    def get(self, request, *args, **kwargs):

        return self.post(request, *args, **kwargs)


class BulkApproveUsersView(LoginRequiredMixin, AdminRequiredMixin, RedirectView):
    """Массовое подтверждение неподтвержденных пользователей"""

    pattern_name = "users:user_list"

    def post(self, request, *args, **kwargs):
        count = User.objects.filter(is_approved=False).update(
            is_approved=True, is_active=True
        )
        messages.success(request, f"Подтверждено {count} пользователей.")
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class DashboardRedirectView(LoginRequiredMixin, RedirectView):
    """Перенаправление на дашборд в зависимости от роли"""

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user

        if user.role == "admin":
            return reverse_lazy("users:admin_dashboard")
        elif user.role == "technologist":
            return reverse_lazy("users:technologist_dashboard")
        elif user.role == "storekeeper":
            return reverse_lazy("users:storekeeper_dashboard")
        elif user.role == "production_master":
            return reverse_lazy("users:production_master_dashboard")
        elif user.role == "otk_senior":
            return reverse_lazy("users:otk_senior_dashboard")
        return reverse_lazy("home")


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Дашборд администратора - только быстрые действия"""

    template_name = "users/dashboards/simple_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quick_actions"] = [
            {
                "url": reverse_lazy("users:user_list"),
                "name": "Управление пользователями",
                "icon": "people",
                "color": "primary",
                "description": "Просмотр и подтверждение пользователей",
            },
            {
                "url": reverse_lazy("blanks:blank_create"),
                "name": "Создать заготовку",
                "icon": "gear",
                "color": "success",
                "description": "Добавить новую заготовку в систему",
            },
            {
                "url": reverse_lazy("products:product_create"),
                "name": "Создать изделие",
                "icon": "box",
                "color": "info",
                "description": "Добавить новое изделие",
            },
            {
                "url": reverse_lazy("warehouse:movement_create"),
                "name": "Новое движение",
                "icon": "arrow-left-right",
                "color": "warning",
                "description": "Создать перемещение заготовок",
            },
            {
                "url": reverse_lazy("production:receipt_create"),
                "name": "Заявка на выдачу",
                "icon": "box-arrow-in-down",
                "color": "danger",
                "description": "Создать заявку на выдачу заготовок",
            },
            {
                "url": reverse_lazy("production:report_create"),
                "name": "Отчет о сборке",
                "icon": "file-text",
                "color": "secondary",
                "description": "Зарегистрировать сборку изделий",
            },
        ]

        return context


class TechnologistDashboardView(
    LoginRequiredMixin, TechnologistRequiredMixin, TemplateView
):
    """Дашборд технолога - только быстрые действия"""

    template_name = "users/dashboards/simple_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quick_actions"] = [
            {
                "url": reverse_lazy("blanks:blank_create"),
                "name": "Создать заготовку",
                "icon": "gear",
                "color": "primary",
                "description": "Добавить новую заготовку",
            },
            {
                "url": reverse_lazy("products:product_create"),
                "name": "Создать изделие",
                "icon": "box",
                "color": "success",
                "description": "Добавить новое изделие",
            },
            {
                "url": reverse_lazy("products:norm_create"),
                "name": "Добавить норму расхода",
                "icon": "file-text",
                "color": "info",
                "description": "Установить нормы расхода для изделия",
            },
            {
                "url": reverse_lazy("blanks:blank_list"),
                "name": "Список заготовок",
                "icon": "list-ul",
                "color": "secondary",
                "description": "Просмотр всех заготовок",
            },
            {
                "url": reverse_lazy("products:product_list"),
                "name": "Список изделий",
                "icon": "boxes",
                "color": "secondary",
                "description": "Просмотр всех изделий",
            },
        ]

        return context


class StorekeeperDashboardView(
    LoginRequiredMixin, StorekeeperRequiredMixin, TemplateView
):
    """Дашборд кладовщика - только быстрые действия"""

    template_name = "users/dashboards/simple_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quick_actions"] = [
            {
                "url": reverse_lazy("warehouse:movement_create"),
                "name": "Новое движение",
                "icon": "arrow-left-right",
                "color": "primary",
                "description": "Создать перемещение заготовок",
            },
            {
                "url": reverse_lazy("warehouse:balance_list"),
                "name": "Остатки на складах",
                "icon": "clipboard-data",
                "color": "success",
                "description": "Просмотр текущих остатков",
            },
            {
                "url": reverse_lazy("warehouse:movement_list"),
                "name": "Журнал движений",
                "icon": "list-ul",
                "color": "info",
                "description": "История всех движений",
            },
            {
                "url": reverse_lazy("production:storekeeper_receipt_list"),
                "name": "Заявки на выдачу",
                "icon": "box-arrow-in-down",
                "color": "warning",
                "description": "Просмотр заявок от производства",
            },
            {
                "url": reverse_lazy("warehouse:warehouse_create"),
                "name": "Добавить склад",
                "icon": "building-add",
                "color": "secondary",
                "description": "Создать новый склад",
            },
        ]

        return context


class ProductionMasterDashboardView(
    LoginRequiredMixin, ProductionMasterRequiredMixin, TemplateView
):
    """Дашборд мастера участка - только быстрые действия"""

    template_name = "users/dashboards/simple_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quick_actions"] = [
            {
                "url": reverse_lazy("production:receipt_create"),
                "name": "Новая заявка",
                "icon": "box-arrow-in-down",
                "color": "primary",
                "description": "Запросить заготовки со склада",
            },
            {
                "url": reverse_lazy("production:report_create"),
                "name": "Отчет о сборке",
                "icon": "file-text",
                "color": "success",
                "description": "Зарегистрировать сборку изделий",
            },
            {
                "url": reverse_lazy("production:balance_list"),
                "name": "Остатки на участке",
                "icon": "pie-chart",
                "color": "info",
                "description": "Текущие остатки заготовок",
            },
            {
                "url": reverse_lazy("production:receipt_list"),
                "name": "Мои заявки",
                "icon": "list-ul",
                "color": "secondary",
                "description": "История заявок на выдачу",
            },
            {
                "url": reverse_lazy("production:report_list"),
                "name": "Отчеты о сборке",
                "icon": "files",
                "color": "secondary",
                "description": "История сборок",
            },
        ]

        return context


class OTKSeniorDashboardView(LoginRequiredMixin, OTKSeniorRequiredMixin, TemplateView):
    """Дашборд старшего контролера ОТК - только быстрые действия"""

    template_name = "users/dashboards/simple_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["quick_actions"] = [
            {
                "url": reverse_lazy("quality_control:defectreport_create"),
                "name": "Новый акт о браке",
                "icon": "file-text",
                "color": "danger",
                "description": "Зарегистрировать брак заготовок",
            },
            {
                "url": reverse_lazy("quality_control:defecttype_create"),
                "name": "Новый вид брака",
                "icon": "tags",
                "color": "success",
                "description": "Добавить вид брака в справочник",
            },
            {
                "url": reverse_lazy("quality_control:defectreport_list")
                + "?confirmed=pending",
                "name": "Акты на подтверждение",
                "icon": "check-circle",
                "color": "warning",
                "description": "Акты, ожидающие подтверждения",
            },
            {
                "url": reverse_lazy("quality_control:defectreport_list"),
                "name": "Все акты",
                "icon": "list-ul",
                "color": "info",
                "description": "История актов о браке",
            },
            {
                "url": reverse_lazy("quality_control:defecttype_list"),
                "name": "Виды брака",
                "icon": "list",
                "color": "secondary",
                "description": "Справочник видов брака",
            },
        ]

        return context
