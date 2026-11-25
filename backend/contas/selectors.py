from django.db.models import Value
from django.db.models.functions import Lower

from .models import Usuario


def buscar_usuario_por_email(*, email: str) -> Usuario | None:
    usuarios = Usuario.objects.exclude(email="").alias(email_normalizado=Lower("email"))
    original = usuarios.filter(email_normalizado=Lower(Value(email))).first()
    if original and original.email != Usuario.objects.normalize_email(original.email):
        return original

    email_normalizado = Usuario.objects.normalize_email(email)
    usuario = original if email_normalizado == email else (
        usuarios.filter(email_normalizado=Lower(Value(email_normalizado))).first()
    )
    if usuario:
        dominio_usuario = Usuario.objects.normalize_email(usuario.email).rpartition("@")[2]
        if dominio_usuario == email_normalizado.rpartition("@")[2]:
            return usuario
    return None
