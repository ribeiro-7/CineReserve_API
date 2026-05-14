from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import PaymentService

def payment_callback(request):
    return JsonResponse({
        "status": "ok",
        "message": "You were redirected after payment!"
    })

@csrf_exempt
def flutterwave_webhook(request):
    return PaymentService.process_flutterwave_webhook(request)