from django.core.exceptions import ValidationError
import re

def password_validator(password):
    if len(password) < 8:
        raise ValidationError("A senha precisar tem no mínimo 8 caracteres.")
    
    # se não achar digito de 0-9
    if not re.search(r'\d', password):
        raise ValidationError("A senha precisar conter pelo menos um caracter numérico.")
    
    #caso não tenha letra maiúscula
    if not re.search(r'[A-Z]', password):
        raise ValidationError("A senha precisar conter pelo menos uma letra maiúscula.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("A senha precisa conter pelo menos um caracter especial")