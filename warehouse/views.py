from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.shortcuts import get_object_or_404, redirect
from .models import Warehouse, StockBalance, StockMovement
from .forms import WarehouseForm, StockBalanceForm, StockMovementForm
from users.views import StorekeeperRequiredMixin, AdminRequiredMixin


class WarehouseListView(LoginRequiredMixin, StorekeeperRequiredMixin, ListView):
    """Список складов"""

    model = Warehouse
    template_name = "warehouse/warehouse_list.html"
    context_object_name = "warehouses"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )
        return queryset


class WarehouseDetailView(LoginRequiredMixin, StorekeeperRequiredMixin, DetailView):
    """Детали склада с остатками"""

    model = Warehouse
    template_name = "warehouse/warehouse_detail.html"
    context_object_name = "warehouse"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["balances"] = (
            StockBalance.objects.filter(warehouse=self.object)
            .select_related("blank")
            .order_by("blank__name")
        )
        return context


class WarehouseCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Создание склада"""

    model = Warehouse
    form_class = WarehouseForm
    template_name = "warehouse/warehouse_form.html"
    success_url = reverse_lazy("warehouse:warehouse_list")

    def form_valid(self, form):
        messages.success(self.request, "Склад успешно создан")
        return super().form_valid(form)


class WarehouseUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Редактирование склада"""

    model = Warehouse
    form_class = WarehouseForm
    template_name = "warehouse/warehouse_form.html"

    def get_success_url(self):
        return reverse_lazy("warehouse:warehouse_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Склад успешно обновлен")
        return super().form_valid(form)


class WarehouseDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление склада"""

    model = Warehouse
    template_name = "warehouse/warehouse_confirm_delete.html"
    success_url = reverse_lazy("warehouse:warehouse_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Склад успешно удален")
        return super().delete(request, *args, **kwargs)


class StockBalanceListView(LoginRequiredMixin, StorekeeperRequiredMixin, ListView):
    """Список остатков"""

    model = StockBalance
    template_name = "warehouse/stockbalance_list.html"
    context_object_name = "balances"
    paginate_by = 50

    def get_queryset(self):
        queryset = StockBalance.objects.select_related("warehouse", "blank").all()

        warehouse_id = self.request.GET.get("warehouse")
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(blank__article__icontains=search) | Q(blank__name__icontains=search)
            )

        low_stock = self.request.GET.get("low_stock")
        if low_stock:
            queryset = queryset.filter(quantity__lte=F("min_stock"))

        return queryset.order_by("warehouse__name", "blank__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        context["current_filters"] = {
            "warehouse": self.request.GET.get("warehouse", ""),
            "search": self.request.GET.get("search", ""),
            "low_stock": self.request.GET.get("low_stock", ""),
        }
        return context


class StockBalanceUpdateView(LoginRequiredMixin, StorekeeperRequiredMixin, UpdateView):
    """Редактирование остатка (минимальный остаток)"""

    model = StockBalance
    form_class = StockBalanceForm
    template_name = "warehouse/stockbalance_form.html"

    def get_success_url(self):
        return reverse_lazy("warehouse:balance_list")

    def form_valid(self, form):
        messages.success(self.request, "Остаток успешно обновлен")
        return super().form_valid(form)


class StockMovementListView(LoginRequiredMixin, StorekeeperRequiredMixin, ListView):
    """Список движений"""

    model = StockMovement
    template_name = "warehouse/stockmovement_list.html"
    context_object_name = "movements"
    paginate_by = 50

    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            "blank", "from_warehouse", "to_warehouse", "created_by"
        ).all()

        movement_type = self.request.GET.get("type")
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search)
                | Q(blank__name__icontains=search)
                | Q(reason__icontains=search)
            )

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(movement_date__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(movement_date__date__lte=date_to)

        return queryset.order_by("-movement_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movement_types"] = StockMovement.MOVEMENT_TYPES
        context["current_filters"] = {
            "type": self.request.GET.get("type", ""),
            "search": self.request.GET.get("search", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
        }
        return context


class StockMovementDetailView(LoginRequiredMixin, StorekeeperRequiredMixin, DetailView):
    """Детали движения"""

    model = StockMovement
    template_name = "warehouse/stockmovement_detail.html"
    context_object_name = "movement"


class StockMovementCreateView(LoginRequiredMixin, StorekeeperRequiredMixin, CreateView):
    """Создание движения (только для кладовщиков и админов)"""

    model = StockMovement
    form_class = StockMovementForm
    template_name = "warehouse/stockmovement_form.html"
    success_url = reverse_lazy("warehouse:movement_list")

    def dispatch(self, request, *args, **kwargs):

        if not (request.user.role == "admin" or request.user.role == "storekeeper"):
            messages.error(request, "У вас нет прав для создания движений")
            return redirect("warehouse:movement_list")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        movement_type = self.request.GET.get("type")
        if movement_type:
            initial["movement_type"] = movement_type
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        self.update_balances(form.instance)

        messages.success(
            self.request, f"Движение {form.instance.number} успешно создано"
        )
        return response

    def update_balances(self, movement):
        """Обновление остатков при движении"""
        from production.models import SiteBalance

        if movement.movement_type == "receipt":

            if movement.to_warehouse:

                balance, _ = StockBalance.objects.get_or_create(
                    warehouse=movement.to_warehouse,
                    blank=movement.blank,
                    defaults={"quantity": 0, "min_stock": 0},
                )
                balance.quantity += movement.quantity
                balance.save()

            elif movement.to_production_site:

                balance, _ = SiteBalance.objects.get_or_create(
                    production_site=movement.to_production_site,
                    blank=movement.blank,
                    defaults={"quantity": 0},
                )
                balance.quantity += movement.quantity
                balance.save()

        elif movement.movement_type == "write_off":

            balance = get_object_or_404(
                StockBalance, warehouse=movement.from_warehouse, blank=movement.blank
            )
            balance.quantity -= movement.quantity
            balance.save()

        elif movement.movement_type == "transfer":

            from_balance = get_object_or_404(
                StockBalance, warehouse=movement.from_warehouse, blank=movement.blank
            )
            from_balance.quantity -= movement.quantity
            from_balance.save()

            if movement.to_warehouse:

                to_balance, _ = StockBalance.objects.get_or_create(
                    warehouse=movement.to_warehouse,
                    blank=movement.blank,
                    defaults={"quantity": 0, "min_stock": 0},
                )
                to_balance.quantity += movement.quantity
                to_balance.save()

            elif movement.to_production_site:

                to_balance, _ = SiteBalance.objects.get_or_create(
                    production_site=movement.to_production_site,
                    blank=movement.blank,
                    defaults={"quantity": 0},
                )
                to_balance.quantity += movement.quantity
                to_balance.save()


class StockReportView(LoginRequiredMixin, StorekeeperRequiredMixin, ListView):
    """Отчет по движениям за период"""

    template_name = "warehouse/stock_report.html"
    context_object_name = "movements"

    def get_queryset(self):
        return StockMovement.objects.select_related(
            "blank", "from_warehouse", "to_warehouse", "created_by"
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        warehouse_id = self.request.GET.get("warehouse")
        movement_type = self.request.GET.get("type")

        queryset = self.get_queryset()

        if date_from:
            queryset = queryset.filter(movement_date__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(movement_date__date__lte=date_to)
        if warehouse_id:
            queryset = queryset.filter(
                Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
            )
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        context["movements"] = queryset.order_by("-movement_date")

        context["total_in"] = (
            queryset.filter(movement_type="receipt").aggregate(total=Sum("quantity"))[
                "total"
            ]
            or 0
        )
        context["total_out"] = (
            queryset.filter(movement_type__in=["write_off", "sale"]).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )
        context["total_transfer"] = (
            queryset.filter(movement_type="transfer").aggregate(total=Sum("quantity"))[
                "total"
            ]
            or 0
        )

        context["warehouses"] = Warehouse.objects.filter(is_active=True)
        context["movement_types"] = StockMovement.MOVEMENT_TYPES

        return context
