from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from rest_framework.exceptions import ValidationError as ErroEntrada
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from escolas.models import Escola

from . import services
from .models import Publicacao
from .permissions import Professor, ProfessorOuAlunoEmLeitura
from .selectors import contexto_docente, publicacoes_visiveis
from .serializers import (
    ContextoSerializer, PeriodoSerializer, PublicacaoSerializer, SaldoSerializer, VersaoSerializer,
)


class ConflitoPublicacao(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A publicação mudou. Abra a versão atual antes de tentar novamente."
    default_code = "publicacao_desatualizada"


def _salvar(request: Request, *, pk: int | None = None) -> Response:
    entrada = PublicacaoSerializer(data=request.data, partial=pk is not None)
    entrada.is_valid(raise_exception=True)
    dados = dict(entrada.validated_data)
    versao = dados.pop("versao", None)
    if pk is not None and versao is None:
        raise ErroEntrada({"versao": "Informe a versão da publicação."})
    try:
        publicacao = services.salvar_publicacao(
            professor=request.user, dados=dados, publicacao_id=pk, versao=versao,
        )
    except ValidationError as erro:
        raise ErroEntrada(erro.message_dict) from erro
    except services.PublicacaoDesatualizada as erro:
        raise ConflitoPublicacao() from erro
    except Publicacao.DoesNotExist as erro:
        raise NotFound() from erro
    except Escola.DoesNotExist as erro:
        raise ErroEntrada({
            "non_field_errors": ["Cadastre a escola antes de publicar atividades."]
        }) from erro
    codigo = status.HTTP_201_CREATED if pk is None else status.HTTP_200_OK
    return Response(PublicacaoSerializer(publicacao).data, status=codigo)


class PublicacoesView(APIView):
    permission_classes = [ProfessorOuAlunoEmLeitura]

    def get(self, request: Request) -> Response:
        publicacoes = publicacoes_visiveis(usuario=request.user)
        return Response(PublicacaoSerializer(publicacoes, many=True).data)

    def post(self, request: Request) -> Response:
        return _salvar(request)


class PublicacaoDetalheView(APIView):
    permission_classes = [ProfessorOuAlunoEmLeitura]

    def get(self, request: Request, pk: int) -> Response:
        publicacao = get_object_or_404(publicacoes_visiveis(usuario=request.user), pk=pk)
        return Response(PublicacaoSerializer(publicacao).data)

    def patch(self, request: Request, pk: int) -> Response:
        return _salvar(request, pk=pk)

    def delete(self, request: Request, pk: int) -> Response:
        entrada = VersaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            services.excluir_publicacao(
                professor=request.user, publicacao_id=pk, **entrada.validated_data,
            )
        except services.PublicacaoDesatualizada as erro:
            raise ConflitoPublicacao() from erro
        except (Publicacao.DoesNotExist, Escola.DoesNotExist) as erro:
            raise NotFound() from erro
        return Response(status=status.HTTP_204_NO_CONTENT)


class ContextoView(APIView):
    permission_classes = [Professor]

    def get(self, request: Request) -> Response:
        contexto = contexto_docente(professor=request.user)
        return Response(ContextoSerializer(contexto, many=True).data)


class SaldoView(APIView):
    permission_classes = [Professor]

    def get(self, request: Request) -> Response:
        periodo = PeriodoSerializer(data=request.query_params)
        periodo.is_valid(raise_exception=True)
        try:
            saldo = services.consultar_saldo(professor=request.user, **periodo.validated_data)
        except ValidationError as erro:
            raise ErroEntrada(erro.message_dict) from erro
        except Escola.DoesNotExist as erro:
            raise NotFound("Cadastre a escola antes de publicar atividades.") from erro
        return Response(SaldoSerializer(saldo).data)
