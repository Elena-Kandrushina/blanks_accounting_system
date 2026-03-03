from django.urls import path
from . import views

app_name = "production"

urlpatterns = [
    # Производственные участки
    path("sites/", views.ProductionSiteListView.as_view(), name="site_list"),
    path(
        "sites/<int:pk>/", views.ProductionSiteDetailView.as_view(), name="site_detail"
    ),
    path("sites/create/", views.ProductionSiteCreateView.as_view(), name="site_create"),
    path(
        "sites/<int:pk>/edit/",
        views.ProductionSiteUpdateView.as_view(),
        name="site_edit",
    ),
    path(
        "sites/<int:pk>/delete/",
        views.ProductionSiteDeleteView.as_view(),
        name="site_delete",
    ),
    # Заявки на выдачу
    path("receipts/", views.BlankReceiptListView.as_view(), name="receipt_list"),
    path(
        "receipts/<int:pk>/",
        views.BlankReceiptDetailView.as_view(),
        name="receipt_detail",
    ),
    path(
        "receipts/create/",
        views.BlankReceiptCreateView.as_view(),
        name="receipt_create",
    ),
    path(
        "receipts/<int:pk>/process/",
        views.BlankReceiptProcessView.as_view(),
        name="receipt_process",
    ),
    path(
        "receipts/<int:pk>/cancel/",
        views.BlankReceiptCancelView.as_view(),
        name="receipt_cancel",
    ),
    # Для кладовщиков
    path(
        "storekeeper/receipts/",
        views.BlankReceiptStorekeeperListView.as_view(),
        name="storekeeper_receipt_list",
    ),
    # Отчеты о сборке
    path("reports/", views.AssemblyReportListView.as_view(), name="report_list"),
    path(
        "reports/<int:pk>/",
        views.AssemblyReportDetailView.as_view(),
        name="report_detail",
    ),
    path(
        "reports/create/",
        views.AssemblyReportCreateView.as_view(),
        name="report_create",
    ),
    path(
        "reports/<int:pk>/delete/",
        views.AssemblyReportDeleteView.as_view(),
        name="report_delete",
    ),
    # Остатки на участках
    path("balances/", views.SiteBalanceListView.as_view(), name="balance_list"),
]
