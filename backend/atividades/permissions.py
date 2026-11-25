from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from contas.models import Usuario


class Professor(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.perfil == Usuario.Perfil.PROFESSOR


class ProfessorOuAlunoEmLeitura(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and (
            request.user.perfil == Usuario.Perfil.PROFESSOR
            or (request.user.perfil == Usuario.Perfil.ALUNO and request.method in SAFE_METHODS)
        )
