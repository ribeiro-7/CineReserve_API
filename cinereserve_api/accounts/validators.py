from django.core.exceptions import ValidationError
import re
from django.contrib.auth import get_user_model

User = get_user_model()

def password_validator(value):
    if len(value) < 8:
        raise ValidationError("Password must contain at least 8 characters.")
    
    if not re.search(r'\d', value):
        raise ValidationError("Password must contain at least one numeric character.")
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must contain at least one upper case character.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Password must contain at least one special character.")
    
def email_validator(value):
    value = value.lower()
    if User.objects.filter(email=value).exists():
        raise ValidationError("An account already exists with that email.")
    return value