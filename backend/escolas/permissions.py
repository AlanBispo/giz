from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from contas.models import Usuario


class CoordenaEscola(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user.is_authenticated
            and request.user.perfil in (Usuario.Perfil.COORDENACAO, Usuario.Perfil.DIRETORIA)
        )


class DirigeEscola(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.perfil == Usuario.Perfil.DIRETORIA
