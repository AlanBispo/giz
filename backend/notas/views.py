from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.exceptions import ValidationError as ErroEntrada
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from atividades.models import Publicacao
from atividades.permissions import Professor
from contas.models import Usuario

from . import services
from .selectors import notas_visiveis
from .serializers import AlteracaoLancamentoSerializer, LancamentoSerializer, NotaConsultaSerializer


class ConsultaNotas(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.perfil in (
            Usuario.Perfil.ALUNO, Usuario.Perfil.COORDENACAO, Usuario.Perfil.DIRETORIA,
        )


class ConflitoLancamento(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "O lançamento ou a publicação mudou. Recarregue antes de salvar novamente."
    default_code = "lancamento_desatualizado"


@method_decorator(never_cache, name="dispatch")
class LancamentoView(APIView):
    permission_classes = [Professor]

    def get(self, request: Request, pk: int) -> Response:
        try:
            lancamento = services.consultar_lancamento(professor=request.user, publicacao_id=pk)
        except Publicacao.DoesNotExist as erro:
            raise NotFound() from erro
        return Response(LancamentoSerializer(lancamento).data)

    def patch(self, request: Request, pk: int) -> Response:
        entrada = AlteracaoLancamentoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            lancamento = services.salvar_lancamento(
                professor=request.user, publicacao_id=pk, **entrada.validated_data,
            )
        except Publicacao.DoesNotExist as erro:
            raise NotFound() from erro
        except services.LancamentoDesatualizado as erro:
            raise ConflitoLancamento() from erro
        except ValidationError as erro:
            raise ErroEntrada(erro.message_dict) from erro
        return Response(LancamentoSerializer(lancamento).data)


@method_decorator(never_cache, name="dispatch")
class NotasView(APIView):
    permission_classes = [ConsultaNotas]

    def get(self, request: Request) -> Response:
        return Response(NotaConsultaSerializer(notas_visiveis(usuario=request.user), many=True).data)
