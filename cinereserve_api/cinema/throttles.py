from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

class SeatsRateThrottle(SimpleRateThrottle):
    scope = 'seat'

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
                return '30/min'
        return '15/min'
    
class SessionReadRateThrottle(SimpleRateThrottle):
    scope = 'session'

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
                return '30/min'
        return '15/min'

class ReserveRateThrottle(UserRateThrottle):
    scope = 'reserve'
    rate = '10/min'

class BuyRateThrottle(UserRateThrottle):
    scope = 'buy'
    rate = '10/min'

class MovieRateThrottle(SimpleRateThrottle):
    scope = 'movie'

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
                return '30/min'
        return '15/min'