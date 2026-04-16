from django.contrib import admin

from .models import Movie, Session

# Configuração para Movie
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'age_rating', 'duration', 'release_date')
    list_filter = ('genre', 'age_rating')
    search_fields = ('title', 'description')

# Configuração para Session
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('movie', 'date', 'showtime', 'theater')
    list_filter = ('date', 'theater')
    search_fields = ('movie__title', 'theater')