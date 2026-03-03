from django import forms
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Форма для создания пользователя"""

    password1 = forms.CharField(
        label=_("Пароль"), widget=forms.PasswordInput, help_text=_("Минимум 8 символов")
    )
    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput,
        help_text=_("Введите тот же пароль для подтверждения"),
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "department",
        )
        labels = {
            "email": _("Email"),
            "first_name": _("Имя"),
            "last_name": _("Фамилия"),
            "phone_number": _("Телефон"),
            "role": _("Роль"),
            "department": _("Подразделение"),
        }
        help_texts = {
            "email": _("Обязательное поле. Используется для входа в систему."),
            "role": _("Выберите роль пользователя в системе."),
            "department": _("Например: Цех №1, Склад, ОТК"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["role"].choices = User.ROLE_CHOICES

        self.fields["role"].required = True

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("Пользователь с таким email уже существует"))
        return email

    def clean(self):
        """Дополнительные проверки"""
        cleaned_data = super().clean()

        role = cleaned_data.get("role")
        is_staff = self.cleaned_data.get("is_staff", False)

        if role == "admin" and not is_staff:
            self.add_error("role", _("Администратор должен иметь статус персонала"))

        return cleaned_data


class UserChangeForm(BaseUserChangeForm):
    """Форма для изменения пользователя"""

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.pop("password", None)


class UserProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователем"""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
        )
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "first_name": _("Имя"),
            "last_name": _("Фамилия"),
            "phone_number": _("Телефон"),
            "avatar": _("Аватар"),
        }


class UserAdminCreationForm(forms.ModelForm):
    """Упрощенная форма для создания пользователя в админке"""

    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Пароли не совпадают"))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
