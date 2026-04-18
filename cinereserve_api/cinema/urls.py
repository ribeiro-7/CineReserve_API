from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'movies', views.MovieViewSet, basename='movies')
router.register(r'sessions', views.SessionViewSet, basename='sessions')

urlpatterns = router.urls