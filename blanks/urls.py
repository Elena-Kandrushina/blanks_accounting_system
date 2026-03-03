from django.urls import path
from . import views

app_name = "blanks"

urlpatterns = [
    path("", views.BlankListView.as_view(), name="blank_list"),
    path("<int:pk>/", views.BlankDetailView.as_view(), name="blank_detail"),
    path("create/", views.BlankCreateView.as_view(), name="blank_create"),
    path("<int:pk>/edit/", views.BlankUpdateView.as_view(), name="blank_edit"),
    path("<int:pk>/delete/", views.BlankDeleteView.as_view(), name="blank_delete"),
]
