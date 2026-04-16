from django.urls import path, include
from rest_framework.routers import DefaultRouter
from booking import views

router = DefaultRouter()
router.register(r'tickets', views.TicketViewSet, basename='tickets')

urlpatterns = router.urls