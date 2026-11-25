from django.contrib.auth import login, logout
from django.db.models import Value
from django.db.models.functions import Lower
from django.http import HttpRequest

from .models import Usuario


def iniciar_sessao(*, request: HttpRequest, email: str, senha: str) -> Usuario | None:
    try:
        usuario = (
            Usuario.objects.exclude(email="")
            .alias(email_normalizado=Lower("email"))
            .get(email_normalizado=Lower(Value(email)))
        )
    except Usuario.DoesNotExist:
        Usuario().set_password(senha)
        return None

    if not usuario.check_password(senha) or not usuario.is_active:
        return None

    login(request, usuario)
    return usuario


def encerrar_sessao(*, request: HttpRequest) -> None:
    logout(request)
