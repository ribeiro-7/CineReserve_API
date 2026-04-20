from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('cinema.urls')),
    path('api/v1/', include('booking.urls')),
    path('api/v1/auth/', include('accounts.urls')),
]