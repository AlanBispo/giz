from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError as ErroEntrada
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from contas.models import Usuario

from . import serializers, services
from .models import AnoLetivo, Bimestre, Disciplina, Escola, Matricula, Turma, VinculoDocente
from .permissions import CoordenaEscola, DirigeEscola
from .selectors import listar_pessoas_escolares


class CadastroViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [CoordenaEscola]

    def salvar(self, serializer: BaseSerializer) -> Model:
        return serializer.save()

    def perform_create(self, serializer: BaseSerializer) -> None:
        try:
            with transaction.atomic():
                serializer.instance = self.salvar(serializer)
        except ValidationError as erro:
            raise ErroEntrada(erro.message_dict) from erro
        except IntegrityError as erro:
            if getattr(erro.__cause__, "sqlstate", None) != "23505":
                raise
            raise ErroEntrada({"non_field_errors": ["Já existe um cadastro com estes dados."]}) from erro


class PessoaViewSet(CadastroViewSet):
    queryset = listar_pessoas_escolares()
    serializer_class = serializers.PessoaSerializer

    def salvar(self, serializer: BaseSerializer) -> Usuario:
        return services.cadastrar_pessoa(**serializer.validated_data)


class AnoLetivoViewSet(CadastroViewSet):
    queryset = AnoLetivo.objects.all()
    serializer_class = serializers.AnoLetivoSerializer


class BimestreViewSet(CadastroViewSet):
    queryset = Bimestre.objects.select_related("ano_letivo")
    serializer_class = serializers.BimestreSerializer


class TurmaViewSet(CadastroViewSet):
    queryset = Turma.objects.select_related("ano_letivo")
    serializer_class = serializers.TurmaSerializer


class DisciplinaViewSet(CadastroViewSet):
    queryset = Disciplina.objects.all()
    serializer_class = serializers.DisciplinaSerializer


class VinculoDocenteViewSet(CadastroViewSet):
    queryset = VinculoDocente.objects.select_related("professor", "turma__ano_letivo", "disciplina")
    serializer_class = serializers.VinculoDocenteSerializer

    def salvar(self, serializer: BaseSerializer) -> VinculoDocente:
        return services.vincular_professor(**serializer.validated_data)


class MatriculaViewSet(CadastroViewSet):
    queryset = Matricula.objects.select_related("aluno", "turma__ano_letivo")
    serializer_class = serializers.MatriculaSerializer

    def salvar(self, serializer: BaseSerializer) -> Matricula:
        return services.matricular_aluno(**serializer.validated_data)


class RegrasView(APIView):
    permission_classes = [DirigeEscola]

    def get(self, request: Request) -> Response:
        escola = get_object_or_404(Escola)
        return Response(serializers.EscolaSerializer(escola).data)

    def patch(self, request: Request) -> Response:
        entrada = serializers.EscolaSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        try:
            escola = services.atualizar_regras(alteracoes=entrada.validated_data)
        except Escola.DoesNotExist as erro:
            raise NotFound("Cadastre a escola no admin do Django.") from erro
        return Response(serializers.EscolaSerializer(escola).data)
