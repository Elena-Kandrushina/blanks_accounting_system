from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    # Склады
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # Остатки
    path('balances/', views.StockBalanceListView.as_view(), name='balance_list'),
    path('balances/<int:pk>/edit/', views.StockBalanceUpdateView.as_view(), name='balance_edit'),

    # Движения
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.StockMovementCreateView.as_view(), name='movement_create'),
    path('movements/<int:pk>/', views.StockMovementDetailView.as_view(), name='movement_detail'),

    # Отчеты
    path('reports/', views.StockReportView.as_view(), name='stock_report'),
]
