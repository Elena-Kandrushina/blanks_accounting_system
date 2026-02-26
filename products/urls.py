from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Изделия
    path('', views.ProductListView.as_view(), name='product_list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Нормы расхода
    path('norms/', views.ConsumptionNormListView.as_view(), name='norm_list'),
    path('norms/<int:pk>/', views.ConsumptionNormDetailView.as_view(), name='norm_detail'),
    path('norms/create/', views.ConsumptionNormCreateView.as_view(), name='norm_create'),
    path('norms/<int:pk>/edit/', views.ConsumptionNormUpdateView.as_view(), name='norm_edit'),
    path('norms/<int:pk>/delete/', views.ConsumptionNormDeleteView.as_view(), name='norm_delete'),
]
