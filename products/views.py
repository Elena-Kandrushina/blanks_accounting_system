from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from users.views import TechnologistRequiredMixin
from .models import Product, ConsumptionNorm
from .forms import ProductForm, ConsumptionNormForm


class ProductListView(LoginRequiredMixin, ListView):
    """Список изделий"""

    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(article__icontains=search)
                | Q(drawing_number__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация об изделии"""

    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["norms"] = self.object.consumption_norms.all()
        return context


class ProductCreateView(
    LoginRequiredMixin, TechnologistRequiredMixin, SuccessMessageMixin, CreateView
):
    """Создание изделия (только технолог)"""

    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    success_message = "Изделие «%(name)s» успешно создано"

    def get_success_url(self):
        return reverse_lazy("products:product_detail", kwargs={"pk": self.object.pk})


class ProductUpdateView(
    LoginRequiredMixin, TechnologistRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Редактирование изделия"""

    model = Product
    form_class = ProductForm
    template_name = "products/product_form.html"
    success_message = "Изделие «%(name)s» успешно обновлено"

    def get_success_url(self):
        return reverse_lazy("products:product_detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(LoginRequiredMixin, TechnologistRequiredMixin, DeleteView):
    """Удаление изделия"""

    model = Product
    template_name = "products/product_confirm_delete.html"
    success_url = reverse_lazy("products:product_list")
    success_message = "Изделие успешно удалено"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ConsumptionNormListView(LoginRequiredMixin, ListView):
    """Список норм расхода"""

    model = ConsumptionNorm
    template_name = "products/norm_list.html"
    context_object_name = "norms"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.GET.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = Product.objects.filter(is_active=True)
        context["current_product"] = self.request.GET.get("product", "")
        return context


class ConsumptionNormDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о норме расхода"""

    model = ConsumptionNorm
    template_name = "products/norm_detail.html"
    context_object_name = "norm"


class ConsumptionNormCreateView(
    LoginRequiredMixin, TechnologistRequiredMixin, SuccessMessageMixin, CreateView
):
    """Создание нормы расхода (добавление заготовки к существующему изделию)"""

    model = ConsumptionNorm
    form_class = ConsumptionNormForm
    template_name = "products/norm_form.html"
    success_message = "Норма расхода успешно создана"

    def get_initial(self):
        initial = super().get_initial()

        product_id = self.request.GET.get("product")
        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
                initial["product"] = product

                self.request.session["last_product_id"] = product_id
            except Product.DoesNotExist:
                pass
        return initial

    def get_success_url(self):

        product_id = self.request.session.get("last_product_id")
        if product_id:
            return reverse_lazy("products:product_detail", kwargs={"pk": product_id})
        return reverse_lazy("products:norm_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product_id = self.request.GET.get("product") or self.request.session.get(
            "last_product_id"
        )
        if product_id:
            try:
                context["selected_product"] = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                pass
        return context


class ConsumptionNormUpdateView(
    LoginRequiredMixin, TechnologistRequiredMixin, SuccessMessageMixin, UpdateView
):
    """Редактирование нормы расхода"""

    model = ConsumptionNorm
    form_class = ConsumptionNormForm
    template_name = "products/norm_form.html"
    success_message = "Норма расхода успешно обновлена"

    def get_success_url(self):
        return reverse_lazy("products:norm_detail", kwargs={"pk": self.object.pk})


class ConsumptionNormDeleteView(
    LoginRequiredMixin, TechnologistRequiredMixin, DeleteView
):
    """Удаление нормы расхода"""

    model = ConsumptionNorm
    template_name = "products/norm_confirm_delete.html"
    success_url = reverse_lazy("products:norm_list")
    success_message = "Норма расхода успешно удалена"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
