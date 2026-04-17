from rest_framework.routers import DefaultRouter
from booking import views

router = DefaultRouter()
router.register(r'bookings', views.BookingViewSet, basename='bookings')
router.register(r'tickets', views.TicketViewSet, basename='tickets')

urlpatterns = router.urls