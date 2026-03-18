from django.urls import path
from . import views


urlpatterns = [
    path('movies/', views.movie_list, name="All Movies List"),
    path('session/', views.session_list, name="Session List"),

]