from django import forms
from .models import Product, ProductCategory, ConsumptionNorm
from blanks.models import Blank


class ProductForm(forms.ModelForm):
    """Форма для создания и редактирования изделия"""

    new_category = forms.CharField(
        max_length=100,
        required=False,
        label="Новая категория",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите название новой категории",
            }
        ),
        help_text="Введите название новой категории, если нужной нет в списке",
    )

    class Meta:
        model = Product
        fields = [
            "article",
            "name",
            "category",
            "new_category",
            "description",
            "drawing",
            "is_active",
        ]
        widgets = {
            "article": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "drawing": forms.FileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "article": "Артикул",
            "name": "Наименование",
            "category": "Категория",
            "description": "Описание",
            "drawing": "Чертеж",
            "is_active": "Активно",
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
            category, created = ProductCategory.objects.get_or_create(
                name=new_category_name,
                defaults={
                    "description": f"Автоматически создана при создании изделия {instance.article}"
                },
            )
            instance.category = category

        if commit:
            instance.save()
        return instance


class ConsumptionNormForm(forms.ModelForm):
    """Форма для норм расхода"""

    class Meta:
        model = ConsumptionNorm
        fields = ["product", "blank", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-control"}),
            "blank": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }
        labels = {
            "product": "Изделие",
            "blank": "Заготовка",
            "quantity": "Количество",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True)
        self.fields["blank"].queryset = Blank.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            pass
        elif "initial" in kwargs and "product" in kwargs["initial"]:
            self.fields["product"].disabled = True
            self.fields["product"].widget.attrs["readonly"] = True

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        blank = cleaned_data.get("blank")

        if product and blank:
            if (
                ConsumptionNorm.objects.filter(product=product, blank=blank)
                .exclude(pk=self.instance.pk if self.instance else None)
                .exists()
            ):
                raise forms.ValidationError(
                    f"Заготовка '{blank.name}' уже добавлена к изделию '{product.name}'"
                )

        return cleaned_data
