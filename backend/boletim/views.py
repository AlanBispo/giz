from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from contas.models import Usuario
from escolas.models import Escola, Turma
from escolas.permissions import CoordenaEscola

from .serializers import BoletimSerializer
from .services import consultar_boletim


class Aluno(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.perfil == Usuario.Perfil.ALUNO


def _responder_boletim(*, usuario: Usuario, turma: Turma | None = None) -> Response:
    try:
        boletim = consultar_boletim(usuario=usuario, turma=turma)
    except Escola.DoesNotExist as erro:
        raise NotFound("Cadastre a escola no admin do Django.") from erro
    return Response(BoletimSerializer(boletim).data)


@method_decorator(never_cache, name="dispatch")
class MeuBoletimView(APIView):
    permission_classes = [Aluno]

    def get(self, request: Request) -> Response:
        return _responder_boletim(usuario=request.user)


@method_decorator(never_cache, name="dispatch")
class BoletimDaTurmaView(APIView):
    permission_classes = [CoordenaEscola]

    def get(self, request: Request, pk: int) -> Response:
        turma = get_object_or_404(Turma, pk=pk)
        return _responder_boletim(usuario=request.user, turma=turma)
