from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

class TicketRateThrottle(UserRateThrottle):
    scope = 'ticket'
    rate = '20/min'

class BookingRateThrottle(UserRateThrottle):
    scope = 'booking'
    rate = '20/min'