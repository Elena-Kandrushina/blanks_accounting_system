from django import forms
from .models import ProductionSite, BlankReceipt, AssemblyReport, SiteBalance
from blanks.models import Blank
from products.models import Product
from warehouse.models import Warehouse
from django.utils import timezone


class ProductionSiteForm(forms.ModelForm):
    """Форма для производственного участка"""

    class Meta:
        model = ProductionSite
        fields = ["name", "code", "warehouse", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "warehouse": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["warehouse"].queryset = Warehouse.objects.filter(is_active=True)
        self.fields["warehouse"].required = False
        self.fields["warehouse"].empty_label = "--- Не привязан ---"


class BlankReceiptForm(forms.ModelForm):
    """Форма для заявки на выдачу заготовок на участок"""

    class Meta:
        model = BlankReceipt
        fields = ["production_site", "blank", "quantity", "receipt_date", "comment"]
        widgets = {
            "receipt_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Комментарий к заявке",
                }
            ),
            "production_site": forms.Select(attrs={"class": "form-control"}),
            "blank": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "production_site": "Участок",
            "blank": "Заготовка",
            "quantity": "Количество",
            "receipt_date": "Дата заявки",
            "comment": "Комментарий",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["blank"].queryset = Blank.objects.filter(is_active=True)
        self.fields["production_site"].queryset = ProductionSite.objects.filter(
            is_active=True
        )

        if "initial" not in kwargs:
            self.fields["receipt_date"].initial = timezone.now()

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity <= 0:
            raise forms.ValidationError("Количество должно быть больше 0")
        return quantity


class AssemblyReportForm(forms.ModelForm):
    """Форма для отчета о сборке"""

    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        label="Изделие",
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="--- Выберите изделие ---",
    )

    production_site = forms.ModelChoiceField(
        queryset=ProductionSite.objects.filter(is_active=True),
        label="Участок",
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="--- Выберите участок ---",
    )

    class Meta:
        model = AssemblyReport
        fields = [
            "product",
            "production_site",
            "quantity",
            "defect_quantity",
            "report_date",
            "comment",
        ]
        widgets = {
            "report_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "defect_quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "product": "Изделие",
            "production_site": "Участок",
            "quantity": "Собрано, шт",
            "defect_quantity": "Брак, шт",
            "report_date": "Дата отчета",
            "comment": "Комментарий",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if "initial" not in kwargs:
            self.fields["report_date"].initial = timezone.now().date()

        self.user = user

    def clean(self):
        cleaned_data = super().clean()

        product = cleaned_data.get("product")
        production_site = cleaned_data.get("production_site")
        quantity = cleaned_data.get("quantity")
        defect_quantity = cleaned_data.get("defect_quantity", 0)

        if not product:
            raise forms.ValidationError("Не выбрано изделие")

        if not production_site:
            raise forms.ValidationError("Не выбран участок")

        if not quantity:
            raise forms.ValidationError("Укажите количество собранных изделий")

        if defect_quantity > quantity:
            raise forms.ValidationError(
                f"Количество брака ({defect_quantity}) не может превышать "
                f"количество собранных изделий ({quantity})"
            )

        norms = product.consumption_norms.all()

        if not norms.exists():
            raise forms.ValidationError(
                f"Для изделия '{product.name}' не заданы нормы расхода. "
                f"Сначала добавьте нормы расхода."
            )

        shortages = []

        for norm in norms:
            blank = norm.blank
            per_unit = norm.quantity
            total_needed = per_unit * quantity

            try:
                balance = SiteBalance.objects.get(
                    production_site=production_site, blank=blank
                )

                if balance.quantity < total_needed:
                    shortages.append(
                        f"{blank.name}: требуется {total_needed} {blank.unit}, "
                        f"в наличии {balance.quantity} {blank.unit}"
                    )

            except SiteBalance.DoesNotExist:
                shortages.append(f"{blank.name}: нет на участке")

        if shortages:
            raise forms.ValidationError(
                "Недостаточно заготовок на участке:\n" + "\n".join(shortages)
            )

        return cleaned_data
