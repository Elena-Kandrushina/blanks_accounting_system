from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Аутентификация
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Профиль
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.CustomPasswordChangeView.as_view(), name='change_password'),

    # Управление пользователями (админка)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/approve/', views.ApproveUserView.as_view(), name='user_approve'),
    path('users/bulk-approve/', views.BulkApproveUsersView.as_view(), name='user_bulk_approve'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # Дашборды
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard_redirect'),
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dashboard/technologist/', views.TechnologistDashboardView.as_view(), name='technologist_dashboard'),
    path('dashboard/storekeeper/', views.StorekeeperDashboardView.as_view(), name='storekeeper_dashboard'),
    path('dashboard/master/', views.ProductionMasterDashboardView.as_view(), name='production_master_dashboard'),
    path('dashboard/otk-senior/', views.OTKSeniorDashboardView.as_view(), name='otk_senior_dashboard'),
]
