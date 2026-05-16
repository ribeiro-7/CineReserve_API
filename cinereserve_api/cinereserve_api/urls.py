from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('cinema.urls')),
    path('api/v1/', include('booking.urls')),
    path('api/v1/auth/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui',),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc',),
]