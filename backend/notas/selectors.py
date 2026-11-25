from decimal import Decimal
from typing import TypedDict

from django.db.models import Max, OuterRef, QuerySet, Subquery

from atividades.models import Publicacao
from contas.models import Usuario
from escolas.models import Matricula

from .models import Nota


class Lancamento(TypedDict):
    publicacao: Publicacao
    alunos: list[Matricula]


def montar_lancamento(*, publicacao: Publicacao) -> Lancamento:
    valores = Nota.objects.filter(publicacao=publicacao, matricula_id=OuterRef("pk")).values("valor")
    alunos = (
        Matricula.objects.filter(turma_id=publicacao.turma_id)
        .select_related("aluno")
        .annotate(valor_nota=Subquery(valores))
        .order_by("aluno__first_name", "aluno__last_name", "pk")
    )
    return {"publicacao": publicacao, "alunos": list(alunos)}


def notas_visiveis(*, usuario: Usuario) -> QuerySet[Nota]:
    notas = Nota.objects.select_related(
        "matricula__aluno", "publicacao__turma__ano_letivo", "publicacao__disciplina",
        "publicacao__bimestre",
    ).order_by("-publicacao__data", "publicacao_id", "matricula__aluno__first_name", "pk")
    if usuario.perfil == Usuario.Perfil.ALUNO:
        return notas.filter(matricula__aluno=usuario)
    if usuario.perfil in (Usuario.Perfil.COORDENACAO, Usuario.Perfil.DIRETORIA):
        return notas
    return notas.none()


def maior_nota_da_publicacao(*, publicacao_id: int) -> Decimal | None:
    return Nota.objects.filter(publicacao_id=publicacao_id).aggregate(maior=Max("valor"))["maior"]
