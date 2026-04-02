from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tickets import views

router = DefaultRouter()
router.register(r'tickets', views.TicketViewSet, basename='tickets')

urlpatterns = router.urls