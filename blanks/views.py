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
from django.db.models import Q
from .models import Blank
from .forms import BlankForm
from users.views import TechnologistRequiredMixin, AdminRequiredMixin


class BlankListView(LoginRequiredMixin, TechnologistRequiredMixin, ListView):
    """Список заготовок"""

    model = Blank
    template_name = "blanks/blank_list.html"
    context_object_name = "blanks"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(article__icontains=search_query) | Q(name__icontains=search_query)
            )
        return queryset


class BlankDetailView(LoginRequiredMixin, TechnologistRequiredMixin, DetailView):
    """Детали заготовки"""

    model = Blank
    template_name = "blanks/blank_detail.html"
    context_object_name = "blank"


class BlankCreateView(LoginRequiredMixin, TechnologistRequiredMixin, CreateView):
    """Создание заготовки"""

    model = Blank
    form_class = BlankForm
    template_name = "blanks/blank_form.html"
    success_url = reverse_lazy("blanks:blank_list")

    def form_valid(self, form):
        messages.success(self.request, "Заготовка успешно создана")
        return super().form_valid(form)


class BlankUpdateView(LoginRequiredMixin, TechnologistRequiredMixin, UpdateView):
    """Редактирование заготовки"""

    model = Blank
    form_class = BlankForm
    template_name = "blanks/blank_form.html"

    def get_success_url(self):
        return reverse_lazy("blanks:blank_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Заготовка успешно обновлена")
        return super().form_valid(form)


class BlankDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Удаление заготовки"""

    model = Blank
    template_name = "blanks/blank_confirm_delete.html"
    success_url = reverse_lazy("blanks:blank_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Заготовка успешно удалена")
        return super().delete(request, *args, **kwargs)
