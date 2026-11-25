from django.contrib.auth import login, logout
from django.http import HttpRequest

from .models import Usuario
from .selectors import buscar_usuario_por_email


def iniciar_sessao(*, request: HttpRequest, email: str, senha: str) -> Usuario | None:
    usuario = buscar_usuario_por_email(email=email)
    if usuario is None:
        Usuario().set_password(senha)
        return None

    if not usuario.check_password(senha) or not usuario.is_active:
        return None

    login(request, usuario)
    return usuario


def encerrar_sessao(*, request: HttpRequest) -> None:
    logout(request)
