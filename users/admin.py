from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User
from .forms import UserAdminCreationForm, UserChangeForm


class UserAdmin(BaseUserAdmin):
    """Админка для кастомной модели пользователя"""

    add_form = UserAdminCreationForm
    form = UserChangeForm

    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "department",
        "is_approved",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "role",
        "is_approved",
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
    )

    list_editable = ("is_approved", "is_active")

    search_fields = ("email", "first_name", "last_name", "phone_number", "department")
    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Личная информация"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "avatar",
                    "department",
                )
            },
        ),
        (
            _("Роли и права"),
            {
                "fields": (
                    "role",
                    "is_approved",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Важные даты"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "department",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("date_joined", "last_login")

    actions = [
        "approve_users",
        "deactivate_users",
        "make_technologist",
        "make_storekeeper",
        "make_production_master",
        "make_otk_senior",
        "make_admin",
    ]

    def approve_users(self, request, queryset):
        """Действие для подтверждения пользователей"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Подтверждено {updated} пользователей")

    approve_users.short_description = "Подтвердить выбранных пользователей"

    def deactivate_users(self, request, queryset):
        """Действие для деактивации пользователей"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано {updated} пользователей")

    deactivate_users.short_description = "Деактивировать выбранных пользователей"

    def make_technologist(self, request, queryset):
        """Назначить роль технолога"""
        updated = queryset.update(role="technologist")
        self.message_user(
            request, f"Назначена роль технолога для {updated} пользователей"
        )

    def make_storekeeper(self, request, queryset):
        """Назначить роль кладовщика"""
        updated = queryset.update(role="storekeeper")
        self.message_user(
            request, f"Назначена роль КЛАДОВЩИК для {updated} пользователей"
        )

    make_storekeeper.short_description = "Назначить роль Кладовщик"

    def make_production_master(self, request, queryset):
        """Назначить роль мастера участка"""
        updated = queryset.update(role="production_master")
        self.message_user(
            request, f"Назначена роль МАСТЕР УЧАСТКА для {updated} пользователей"
        )

    make_production_master.short_description = "Назначить роль Мастер участка"

    def make_otk_senior(self, request, queryset):
        """Назначить роль старшего контролера ОТК"""
        updated = queryset.update(role="otk_senior")
        self.message_user(
            request, f"Назначена роль СТАРШИЙ КОНТРОЛЕР ОТК для {updated} пользователей"
        )

    make_otk_senior.short_description = "Назначить роль Старший контролер ОТК"

    def make_admin(self, request, queryset):
        """Назначить роль администратора"""
        updated = queryset.update(role="admin")
        self.message_user(
            request, f"Назначена роль АДМИНИСТРАТОР для {updated} пользователей"
        )

    make_admin.short_description = "Назначить роль Администратор"

    make_technologist.short_description = "Назначить роль технолога"

    def get_queryset(self, request):
        """Администраторы видят всех пользователей"""
        return super().get_queryset(request)

    def get_form(self, request, obj=None, **kwargs):
        """Кастомизация формы в зависимости от действия"""
        form = super().get_form(request, obj, **kwargs)

        if obj:
            form.base_fields.pop("password1", None)
            form.base_fields.pop("password2", None)

        return form


admin.site.register(User, UserAdmin)
