from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from production.models import ProductionSite
from .models import DefectType, DefectReport
from .forms import DefectTypeForm, DefectReportForm
from users.views import OTKSeniorRequiredMixin


class DefectTypeListView(LoginRequiredMixin, OTKSeniorRequiredMixin, ListView):
    """Список видов брака"""

    model = DefectType
    template_name = "quality_control/defecttype_list.html"
    context_object_name = "defect_types"
    paginate_by = 20


class DefectTypeCreateView(LoginRequiredMixin, OTKSeniorRequiredMixin, CreateView):
    """Создание вида брака"""

    model = DefectType
    form_class = DefectTypeForm
    template_name = "quality_control/defecttype_form.html"
    success_url = reverse_lazy("quality_control:defecttype_list")


class DefectTypeUpdateView(LoginRequiredMixin, OTKSeniorRequiredMixin, UpdateView):
    """Редактирование вида брака"""

    model = DefectType
    form_class = DefectTypeForm
    template_name = "quality_control/defecttype_form.html"
    success_url = reverse_lazy("quality_control:defecttype_list")

    def form_valid(self, form):
        messages.success(self.request, "Вид брака успешно обновлен")
        return super().form_valid(form)


class DefectReportListView(LoginRequiredMixin, OTKSeniorRequiredMixin, ListView):
    """Список актов о браке"""

    model = DefectReport
    template_name = "quality_control/defectreport_list.html"
    context_object_name = "reports"
    paginate_by = 50

    def get_queryset(self):
        queryset = DefectReport.objects.select_related(
            "production_site", "blank", "defect_type", "detected_by", "confirmed_by"
        ).all()

        site_id = self.request.GET.get("site")
        if site_id:
            queryset = queryset.filter(production_site_id=site_id)

        confirmed = self.request.GET.get("confirmed")
        if confirmed == "confirmed":
            queryset = queryset.filter(is_confirmed=True)
        elif confirmed == "pending":
            queryset = queryset.filter(is_confirmed=False)

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(number__icontains=search)
                | Q(blank__name__icontains=search)
                | Q(description__icontains=search)
            )

        return queryset.order_by("-report_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sites"] = ProductionSite.objects.filter(is_active=True)
        return context


class DefectReportCreateView(LoginRequiredMixin, OTKSeniorRequiredMixin, CreateView):
    """Создание акта о браке"""

    model = DefectReport
    form_class = DefectReportForm
    template_name = "quality_control/defectreport_form.html"
    success_url = reverse_lazy("quality_control:defectreport_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["detected_by"] = self.request.user
        return initial

    def form_valid(self, form):
        form.instance.detected_by = self.request.user
        messages.success(self.request, "Акт о браке успешно создан")
        return super().form_valid(form)


class DefectReportConfirmView(LoginRequiredMixin, OTKSeniorRequiredMixin, UpdateView):
    """Подтверждение акта о браке (списание заготовок)"""

    model = DefectReport
    fields = []
    template_name = "quality_control/defectreport_confirm.html"
    context_object_name = "report"

    def get_success_url(self):
        return reverse_lazy(
            "quality_control:defectreport_detail", kwargs={"pk": self.object.pk}
        )

    def form_valid(self, form):

        self.object.is_confirmed = True
        self.object.confirmed_by = self.request.user
        self.object.confirmed_at = timezone.now()

        self.object.save()
        messages.success(
            self.request, f"Акт {self.object.number} подтвержден, заготовки списаны"
        )
        return super().form_valid(form)


class DefectReportDetailView(LoginRequiredMixin, OTKSeniorRequiredMixin, DetailView):
    """Детали акта о браке"""

    model = DefectReport
    template_name = "quality_control/defectreport_detail.html"
    context_object_name = "report"
