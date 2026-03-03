from django import forms
from .models import Blank, BlankCategory


class BlankForm(forms.ModelForm):
    """Форма для создания и редактирования заготовки"""

    new_category = forms.CharField(
        max_length=100,
        required=False,
        label="Новая категория",
        help_text="Введите название новой категории, если нужной нет в списке",
    )

    class Meta:
        model = Blank
        fields = [
            "article",
            "name",
            "category",
            "new_category",
            "unit",
            "weight",
            "description",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "article": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-control"}),
            "weight": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "article": "Артикул",
            "name": "Наименование",
            "category": "Категория (выберите из списка)",
            "unit": "Единица измерения",
            "weight": "Вес (кг)",
            "description": "Описание",
            "is_active": "Активна",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Выберите категорию или создайте новую"

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category")

        if not category and not new_category:
            raise forms.ValidationError(
                "Выберите существующую категорию или введите новую"
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_category_name = self.cleaned_data.get("new_category")

        if new_category_name and not self.cleaned_data.get("category"):
            category, created = BlankCategory.objects.get_or_create(
                name=new_category_name,
                defaults={
                    "description": f"Автоматически создана при создании заготовки {instance.article}"
                },
            )
            instance.category = category

        if commit:
            instance.save()
        return instance


class BlankCategoryForm(forms.ModelForm):
    """Форма для категории заготовок"""

    class Meta:
        model = BlankCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
