from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from users.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Приложения
    path('', HomeView.as_view(), name='home'),
    path('users/', include('users.urls', namespace='users')),
    path('blanks/', include('blanks.urls', namespace='blanks')),
    path('products/', include('products.urls', namespace='products')),
    path('warehouse/', include('warehouse.urls', namespace='warehouse')),
    path('production/', include('production.urls', namespace='production')),
    path('quality-control/', include('quality_control.urls', namespace='quality_control')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
