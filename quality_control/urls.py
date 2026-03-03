from django.urls import path
from . import views

app_name = 'quality_control'

urlpatterns = [
    # Виды брака
    path('defect-types/', views.DefectTypeListView.as_view(), name='defecttype_list'),
    path('defect-types/create/', views.DefectTypeCreateView.as_view(), name='defecttype_create'),
    path('defect-types/<int:pk>/edit/', views.DefectTypeUpdateView.as_view(), name='defecttype_edit'),

    # Акты о браке
    path('defect-reports/', views.DefectReportListView.as_view(), name='defectreport_list'),
    path('defect-reports/create/', views.DefectReportCreateView.as_view(), name='defectreport_create'),
    path('defect-reports/<int:pk>/', views.DefectReportDetailView.as_view(), name='defectreport_detail'),
    path('defect-reports/<int:pk>/confirm/', views.DefectReportConfirmView.as_view(), name='defectreport_confirm'),
]
