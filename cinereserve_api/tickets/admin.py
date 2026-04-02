from django.contrib import admin

from tickets.models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'purchased_at', 'seat_session')
    list_filter = ('code', 'purchased_at')
    search_fields = ('id', 'code')