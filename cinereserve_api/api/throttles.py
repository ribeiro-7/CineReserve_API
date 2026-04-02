from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from rest_framework.throttling import SimpleRateThrottle

class SeatsRateThrottle(SimpleRateThrottle):
    scope = 'seats'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f"{self.scope}_user_{request.user.id}"
        else:
            ident = self.get_ident(request)
            return f"{self.scope}_anon_{ident}"

    def get_rate(self):
        if hasattr(self, 'request'):
            request = self.request
            if request.user and request.user.is_authenticated:
                return '20/min'
        return '5/min'

class ReserveRateThrottle(UserRateThrottle):
    scope = 'reserve'
    rate = '5/min'

class BuyRateThrottle(UserRateThrottle):
    scope = 'buy'
    rate = '5/min'

class TicketRateThrottle(UserRateThrottle):
    scope = 'ticket'
    rate = '30/min'