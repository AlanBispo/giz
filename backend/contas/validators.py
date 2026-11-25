from django.contrib.auth.password_validation import MinimumLengthValidator
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, validate_email

from .models import Usuario

LIMITE_SENHA = 4096


def validar_email_normalizado(email: str) -> None:
    normalizado = Usuario.objects.normalize_email(email)
    limite = Usuario._meta.get_field("email").max_length
    if len(normalizado) > limite:
        raise ValidationError(f"O e-mail normalizado deve ter até {limite} caracteres.")
    validate_email(normalizado)


class SenhaComprimentoValidator(MinimumLengthValidator):
    def validate(self, password: str, user: Usuario | None = None) -> None:
        MaxLengthValidator(LIMITE_SENHA)(password)
        super().validate(password.strip(), user)
