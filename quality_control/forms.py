from django import forms
from .models import DefectType, DefectReport
from production.models import ProductionSite
from blanks.models import Blank


class DefectTypeForm(forms.ModelForm):
    class Meta:
        model = DefectType
        fields = ["code", "name", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class DefectReportForm(forms.ModelForm):
    """Форма для акта о браке с возможностью создания нового вида брака"""

    defect_type = forms.ModelChoiceField(
        queryset=DefectType.objects.filter(is_active=True),
        required=False,
        label="Вид брака (выбрать из списка)",
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="--- Выберите существующий вид брака ---",
    )

    new_defect_type_code = forms.CharField(
        max_length=20,
        required=False,
        label="Код нового вида брака",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Например: ТРЕЩ, СКОЛ, ЦАР"}
        ),
    )

    new_defect_type_name = forms.CharField(
        max_length=100,
        required=False,
        label="Название нового вида брака",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например: Трещина, Скол, Царапина",
            }
        ),
    )

    new_defect_type_description = forms.CharField(
        required=False,
        label="Описание нового вида брака",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Описание нового вида брака",
            }
        ),
    )

    class Meta:
        model = DefectReport
        fields = [
            "production_site",
            "blank",
            "quantity",
            "defect_type",
            "new_defect_type_code",
            "new_defect_type_name",
            "new_defect_type_description",
            "description",
            "photo",
        ]
        widgets = {
            "production_site": forms.Select(attrs={"class": "form-control"}),
            "blank": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Подробное описание брака",
                }
            ),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["production_site"].queryset = ProductionSite.objects.filter(
            is_active=True
        )
        self.fields["blank"].queryset = Blank.objects.filter(is_active=True)

        self.fields["defect_type"].required = False
        self.fields["new_defect_type_code"].required = False
        self.fields["new_defect_type_name"].required = False
        self.fields["new_defect_type_description"].required = False

    def clean(self):
        cleaned_data = super().clean()
        defect_type = cleaned_data.get("defect_type")
        new_code = cleaned_data.get("new_defect_type_code")
        new_name = cleaned_data.get("new_defect_type_name")

        if not defect_type and not new_code and not new_name:
            raise forms.ValidationError(
                "Выберите существующий вид брака или заполните поля для нового вида"
            )

        if new_code or new_name:
            if not new_code:
                raise forms.ValidationError("Для нового вида брака укажите код")
            if not new_name:
                raise forms.ValidationError("Для нового вида брака укажите название")

            if DefectType.objects.filter(code=new_code).exists():
                raise forms.ValidationError(
                    f"Вид брака с кодом '{new_code}' уже существует"
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        new_code = self.cleaned_data.get("new_defect_type_code")
        new_name = self.cleaned_data.get("new_defect_type_name")
        new_description = self.cleaned_data.get("new_defect_type_description")

        if new_code and new_name:

            defect_type = DefectType.objects.create(
                code=new_code,
                name=new_name,
                description=new_description
                or f"Автоматически создан при создании акта {instance.number}",
                is_active=True,
            )
            instance.defect_type = defect_type

        if commit:
            instance.save()

        return instance
