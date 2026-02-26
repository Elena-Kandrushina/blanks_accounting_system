from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from products.models import Product
from warehouse.models import StockBalance
from .models import ProductionSite, BlankReceipt, AssemblyReport, SiteBalance
from .forms import ProductionSiteForm, BlankReceiptForm, AssemblyReportForm
from users.views import (
    ProductionRequiredMixin,
    ProductionMasterRequiredMixin,
    AdminRequiredMixin,
)


class ProductionSiteListView(
    LoginRequiredMixin, ProductionMasterRequiredMixin, ListView
):
    """Список производственных участков"""

    model = ProductionSite
    template_name = "production/site_list.html"
    context_object_name = "sites"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )
        return queryset


class ProductionSiteDetailView(LoginRequiredMixin, ProductionRequiredMixin, DetailView):
    """Детали производственного участка"""

    model = ProductionSite
    template_name = "production/site_detail.html"
    context_object_name = "site"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["balances"] = SiteBalance.objects.filter(
            production_site=self.object
        ).select_related("blank")

        context["recent_receipts"] = BlankReceipt.objects.filter(
            production_site=self.object
        ).order_by("-receipt_date")[:10]

        if self.object.warehouse:
            context["warehouse_balances"] = StockBalance.objects.filter(
                warehouse=self.object.warehouse
            ).select_related("blank")[:10]

        return context


class ProductionSiteCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Создание производственного участка"""

    model = ProductionSite
    form_class = ProductionSiteForm
    template_name = "production/site_form.html"
    success_url = reverse_lazy("production:site_list")

    def form_valid(self, form):
        messages.success(self.request, "Производственный участок успешно создан")
        return super().form_valid(form)


class ProductionSiteUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Редактирование производственного участка"""

    model = ProductionSite
    form_class = ProductionSiteForm
    template_name = "production/site_form.html"

    def get_success_url(self):
        return reverse_lazy("production:site_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Производственный участок успешно обновлен")
        return super().form_valid(form)


class ProductionSiteDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление производственного участка"""

    model = ProductionSite
    template_name = "production/site_confirm_delete.html"
    success_url = reverse_lazy("production:site_list")
    context_object_name = "site"

    def delete(self, request, *args, **kwargs):
        site = self.get_object()
        messages.success(request, f"Участок {site.code} успешно удален")
        return super().delete(request, *args, **kwargs)


class BlankReceiptListView(LoginRequiredMixin, ProductionRequiredMixin, ListView):
    """Список заявок на выдачу заготовок"""

    model = BlankReceipt
    template_name = "production/receipt_list.html"
    context_object_name = "receipts"
    paginate_by = 50

    def get_queryset(self):
        queryset = BlankReceipt.objects.select_related(
            "production_site", "blank", "created_by", "processed_by"
        ).all()

        site_id = self.request.GET.get("site")
        if site_id:
            queryset = queryset.filter(production_site_id=site_id)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(receipt_date__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(receipt_date__date__lte=date_to)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(blank__name__icontains=search)
            )

        return queryset.order_by("-receipt_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sites"] = ProductionSite.objects.filter(is_active=True)

        context["can_create"] = self.request.user.role in ["admin", "production_master"]
        return context


class BlankReceiptStorekeeperListView(
    LoginRequiredMixin, UserPassesTestMixin, ListView
):
    """Список заявок для кладовщиков"""

    model = BlankReceipt
    template_name = "production/receipt_list.html"
    context_object_name = "receipts"
    paginate_by = 50

    def test_func(self):

        return self.request.user.role == "storekeeper" or self.request.user.is_superuser

    def get_queryset(self):
        queryset = BlankReceipt.objects.select_related(
            "production_site", "blank", "created_by", "processed_by"
        ).all()

        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        site_id = self.request.GET.get("site")
        if site_id:
            queryset = queryset.filter(production_site_id=site_id)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(receipt_date__date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(receipt_date__date__lte=date_to)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search) | Q(blank__name__icontains=search)
            )

        return queryset.order_by("-receipt_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sites"] = ProductionSite.objects.filter(is_active=True)
        context["status_choices"] = BlankReceipt.STATUS_CHOICES
        context["can_create"] = False
        context["is_storekeeper_view"] = True
        return context


class BlankReceiptDetailView(LoginRequiredMixin, DetailView):
    """Детали заявки на выдачу - доступно всем авторизованным"""

    model = BlankReceipt
    template_name = "production/receipt_detail.html"
    context_object_name = "receipt"
    pk_url_kwarg = "pk"


class BlankReceiptCreateView(
    LoginRequiredMixin, ProductionMasterRequiredMixin, CreateView
):
    """Создание заявки на выдачу заготовок (только для мастеров)"""

    model = BlankReceipt
    form_class = BlankReceiptForm
    template_name = "production/receipt_form.html"
    success_url = reverse_lazy("production:receipt_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.status = "new"
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Заявка {self.object.number} успешно создана и отправлена кладовщику",
        )
        return response


class BlankReceiptProcessView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Обработка заявки кладовщиком (выдача заготовок)"""

    model = BlankReceipt
    fields = []
    template_name = "production/receipt_process.html"
    context_object_name = "receipt"
    pk_url_kwarg = "pk"

    def test_func(self):

        return self.request.user.role == "storekeeper" or self.request.user.is_superuser

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse_lazy("production:receipt_list")
        return reverse_lazy("production:storekeeper_receipt_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # print("\n" + "=" * 50)
        # print(f"НАЧАЛО ОБРАБОТКИ ЗАЯВКИ {self.object.number}")
        # print("=" * 50)
        # print(f"Текущий статус: {self.object.status}")
        # print(f"Текущий processed_by: {self.object.processed_by}")
        # print(f"Текущий completed_date: {self.object.completed_date}")
        # print(f"Пользователь: {request.user.email}")
        # print(f"Superuser: {request.user.is_superuser}")
        # print(f"Роль: {request.user.role}")

        if self.object.status != "new":
            messages.error(
                request, f"Заявка уже в статусе {self.object.get_status_display()}"
            )
            # print(f"ОШИБКА: статус не new, а {self.object.status}")
            return redirect(self.get_success_url())

        warehouse = self.object.production_site.warehouse
        if not warehouse:
            messages.error(request, "У участка не привязан склад")
            # print(f"ОШИБКА: нет склада у участка {self.object.production_site.code}")
            return redirect(self.get_success_url())

        # print(f"Склад: {warehouse.code} - {warehouse.name}")

        try:
            from warehouse.models import StockBalance, StockMovement

            # print(f"Ищем остаток на складе {warehouse.code} для заготовки {self.object.blank.name}")

            balance = StockBalance.objects.get(
                warehouse=warehouse, blank=self.object.blank
            )

            print(f"Остаток на складе: {balance.quantity}")
            print(f"Требуется: {self.object.quantity}")

            if balance.quantity < self.object.quantity:
                messages.error(
                    request,
                    f"Недостаточно заготовок на складе. Доступно: {balance.quantity}",
                )
                # print(f"ОШИБКА: недостаточно заготовок")
                return redirect(self.get_success_url())

            balance.quantity -= self.object.quantity
            balance.save()
            # print(f"Новый остаток на складе: {balance.quantity}")

            from production.models import SiteBalance

            site_balance, created = SiteBalance.objects.get_or_create(
                production_site=self.object.production_site,
                blank=self.object.blank,
                defaults={"quantity": 0},
            )
            site_balance.quantity += self.object.quantity
            site_balance.save()
            # print(f"Остаток на участке: {site_balance.quantity} (создан: {created})")

            movement = StockMovement.objects.create(
                movement_type="transfer",
                from_warehouse=warehouse,
                to_production_site=self.object.production_site,
                blank=self.object.blank,
                quantity=self.object.quantity,
                movement_date=timezone.now(),
                reason=f"Выдача по заявке {self.object.number}",
                receipt_request=self.object,
                created_by=request.user,
            )
            # print(f"Создано движение: {movement.number}")

            # print("Обновляем статус заявки...")
            self.object.status = "completed"
            self.object.processed_by = request.user
            self.object.completed_date = timezone.now()
            self.object.source_info = (
                f"Выдано со склада {warehouse.code} (движение {movement.number})"
            )
            self.object.save()

            self.object.refresh_from_db()

            # print(f"СТАТУС ПОСЛЕ СОХРАНЕНИЯ: {self.object.status}")
            # print(f"PROCESSED_BY: {self.object.processed_by}")
            # print(f"COMPLETED_DATE: {self.object.completed_date}")
            # print(f"SOURCE_INFO: {self.object.source_info}")

            messages.success(
                request,
                f"✅ Заявка {self.object.number} выполнена! Статус: {self.object.status}",
            )

        except StockBalance.DoesNotExist:
            messages.error(
                request,
                f"На складе {warehouse.code} нет заготовок {self.object.blank.name}",
            )
            # print(f"ОШИБКА: нет остатков на складе")
        except Exception as e:
            messages.error(request, f"Ошибка при обработке заявки: {str(e)}")
            # print(f"ИСКЛЮЧЕНИЕ: {str(e)}")
            import traceback

            traceback.print_exc()

        # print("=" * 50)
        # print("КОНЕЦ ОБРАБОТКИ")
        # print("=" * 50 + "\n")

        return redirect(self.get_success_url())


class BlankReceiptCancelView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Отмена заявки мастером"""

    model = BlankReceipt
    fields = []
    template_name = "production/receipt_cancel.html"
    context_object_name = "receipt"
    pk_url_kwarg = "pk"

    def test_func(self):

        return (
            self.request.user.role == "production_master"
            or self.request.user.is_superuser
        )

    def get_success_url(self):
        return reverse_lazy("production:receipt_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        reason = request.POST.get("reason", "")
        success, message = self.object.cancel(request.user, reason)

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect(self.get_success_url())


class AssemblyReportCreateView(LoginRequiredMixin, ProductionRequiredMixin, CreateView):
    """Создание отчета о сборке"""

    model = AssemblyReport
    form_class = AssemblyReportForm
    template_name = "production/report_form.html"
    success_url = reverse_lazy("production:report_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.produced_by = self.request.user
        messages.success(
            self.request, "Отчет о сборке успешно создан, заготовки списаны"
        )
        return super().form_valid(form)


class AssemblyReportDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление отчета о сборке"""

    model = AssemblyReport
    template_name = "production/report_confirm_delete.html"
    success_url = reverse_lazy("production:report_list")
    context_object_name = "report"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Отчет успешно удален")
        return super().delete(request, *args, **kwargs)


class AssemblyReportListView(LoginRequiredMixin, ProductionRequiredMixin, ListView):
    """Список отчетов о сборке"""

    model = AssemblyReport
    template_name = "production/report_list.html"
    context_object_name = "reports"
    paginate_by = 50

    def get_queryset(self):
        queryset = AssemblyReport.objects.select_related(
            "product", "production_site", "produced_by"
        ).all()

        product_id = self.request.GET.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        site_id = self.request.GET.get("site")
        if site_id:
            queryset = queryset.filter(production_site_id=site_id)

        date_from = self.request.GET.get("date_from")
        if date_from:
            queryset = queryset.filter(report_date__gte=date_from)

        date_to = self.request.GET.get("date_to")
        if date_to:
            queryset = queryset.filter(report_date__lte=date_to)

        return queryset.order_by("-report_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.filter(is_active=True)
        context["sites"] = ProductionSite.objects.filter(is_active=True)
        return context


class AssemblyReportDetailView(LoginRequiredMixin, ProductionRequiredMixin, DetailView):
    """Детали отчета о сборке"""

    model = AssemblyReport
    template_name = "production/report_detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        consumed_blanks = []
        norms = self.object.product.consumption_norms.all()

        for norm in norms:
            total_consumed = norm.quantity * self.object.quantity
            consumed_blanks.append(
                {
                    "blank": norm.blank,
                    "per_unit": norm.quantity,
                    "total": total_consumed,
                    "unit": norm.blank.unit,
                }
            )

        context["consumed_blanks"] = consumed_blanks
        context["total_blanks_consumed"] = sum(
            item["total"] for item in consumed_blanks
        )

        return context


class SiteBalanceListView(LoginRequiredMixin, ProductionRequiredMixin, ListView):
    """Остатки на участках"""

    model = SiteBalance
    template_name = "production/site_balance_list.html"
    context_object_name = "balances"
    paginate_by = 50

    def get_queryset(self):
        queryset = SiteBalance.objects.select_related("production_site", "blank").all()

        site_id = self.request.GET.get("site")
        if site_id:
            queryset = queryset.filter(production_site_id=site_id)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(blank__name__icontains=search) | Q(blank__article__icontains=search)
            )

        return queryset.order_by("production_site__name", "blank__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sites"] = ProductionSite.objects.filter(is_active=True)
        return context
