from django import forms
from .models import Warehouse, StockBalance, StockMovement
from blanks.models import Blank
from production.models import ProductionSite


class WarehouseForm(forms.ModelForm):
    """Форма для склада"""

    class Meta:
        model = Warehouse
        fields = ["name", "code", "address", "is_active"]


class StockBalanceForm(forms.ModelForm):
    """Форма для остатков"""

    class Meta:
        model = StockBalance
        fields = ["warehouse", "blank", "quantity", "min_stock"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "min_stock": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }


class StockMovementForm(forms.ModelForm):
    """Форма для движения заготовок"""

    class Meta:
        model = StockMovement
        fields = [
            "movement_type",
            "from_warehouse",
            "to_warehouse",
            "to_production_site",
            "blank",
            "quantity",
            "movement_date",
            "reason",
            "comment",
        ]
        widgets = {
            "movement_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "reason": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Накладная №123",
                }
            ),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "movement_type": forms.Select(attrs={"class": "form-control"}),
            "from_warehouse": forms.Select(attrs={"class": "form-control"}),
            "to_warehouse": forms.Select(attrs={"class": "form-control"}),
            "to_production_site": forms.Select(attrs={"class": "form-control"}),
            "blank": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["blank"].queryset = Blank.objects.filter(is_active=True)
        self.fields["to_production_site"].queryset = ProductionSite.objects.filter(
            is_active=True
        )

        self.fields["from_warehouse"].empty_label = "Выберите склад"
        self.fields["to_warehouse"].empty_label = "Выберите склад"
        self.fields["to_production_site"].empty_label = "Выберите участок"

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get("movement_type")
        from_warehouse = cleaned_data.get("from_warehouse")
        to_warehouse = cleaned_data.get("to_warehouse")
        to_production_site = cleaned_data.get("to_production_site")
        blank = cleaned_data.get("blank")
        quantity = cleaned_data.get("quantity")

        if movement_type == "transfer":
            if not from_warehouse:
                raise forms.ValidationError(
                    "Для перемещения нужно указать склад отправитель"
                )
            if not to_warehouse and not to_production_site:
                raise forms.ValidationError(
                    "Для перемещения нужно указать склад получатель или участок"
                )
            if to_warehouse and to_production_site:
                raise forms.ValidationError(
                    "Укажите только одно: склад получатель или участок"
                )

        elif movement_type == "receipt":
            if not to_warehouse and not to_production_site:
                raise forms.ValidationError(
                    "Для поступления нужно указать склад получатель или участок"
                )
            if to_warehouse and to_production_site:
                raise forms.ValidationError(
                    "Укажите только одно: склад получатель или участок"
                )
            if from_warehouse:
                raise forms.ValidationError(
                    "Для поступления не нужно указывать склад отправитель"
                )

        elif movement_type == "write_off":
            if not from_warehouse:
                raise forms.ValidationError("Для списания нужно указать склад")
            if to_warehouse or to_production_site:
                raise forms.ValidationError(
                    "Для списания не нужно указывать получателя"
                )

        if (
            movement_type in ["transfer", "write_off"]
            and from_warehouse
            and blank
            and quantity
        ):
            try:
                from .models import StockBalance

                balance = StockBalance.objects.get(
                    warehouse=from_warehouse, blank=blank
                )
                if balance.quantity < quantity:
                    raise forms.ValidationError(
                        f"Недостаточно заготовок на складе. Доступно: {balance.quantity}"
                    )
            except StockBalance.DoesNotExist:
                raise forms.ValidationError(f"На складе нет заготовок {blank.name}")

        return cleaned_data
