from collections import defaultdict
from decimal import Decimal

from django.db.models import Exists, OuterRef, QuerySet, Sum

from contas.models import Usuario
from escolas.models import Bimestre, Disciplina, Matricula, Turma, VinculoDocente

from .models import Publicacao


def vinculos_do_professor(*, professor: Usuario) -> QuerySet[VinculoDocente]:
    return VinculoDocente.objects.filter(professor=professor)


def contexto_docente(*, professor: Usuario) -> list[dict]:
    vinculos = list(vinculos_do_professor(professor=professor).select_related(
        "turma__ano_letivo", "disciplina"
    ).order_by("-turma__ano_letivo__ano", "turma__nome", "disciplina__nome", "pk"))
    bimestres = defaultdict(list)
    for bimestre in Bimestre.objects.filter(ano_letivo_id__in={
        vinculo.turma.ano_letivo_id for vinculo in vinculos
    }):
        bimestres[bimestre.ano_letivo_id].append(bimestre)

    return [
        {"vinculo": vinculo, "bimestres": bimestres[vinculo.turma.ano_letivo_id]}
        for vinculo in vinculos
    ]


def publicacoes_visiveis(*, usuario: Usuario) -> QuerySet[Publicacao]:
    publicacoes = Publicacao.objects.select_related("turma__ano_letivo", "disciplina", "bimestre")
    if usuario.perfil == Usuario.Perfil.PROFESSOR:
        return publicacoes.filter(Exists(vinculos_do_professor(professor=usuario).filter(
            turma_id=OuterRef("turma_id"), disciplina_id=OuterRef("disciplina_id"),
        )))
    if usuario.perfil == Usuario.Perfil.ALUNO:
        return publicacoes.filter(turma_id__in=Matricula.objects.filter(aluno=usuario).values("turma_id"))
    return publicacoes.none()


def publicacoes_do_periodo(
    *, turma: Turma, disciplina: Disciplina, bimestre: Bimestre
) -> QuerySet[Publicacao]:
    return Publicacao.objects.filter(turma=turma, disciplina=disciplina, bimestre=bimestre)


def somar_atividades(*, publicacoes: QuerySet[Publicacao]) -> Decimal:
    return publicacoes.filter(tipo=Publicacao.Tipo.ATIVIDADE).aggregate(
        total=Sum("valor", default=Decimal("0.00"))
    )["total"]


def ha_periodo_acima_do_limite(*, limite: Decimal) -> bool:
    return (
        Publicacao.objects.filter(tipo=Publicacao.Tipo.ATIVIDADE)
        .order_by()
        .values("turma_id", "disciplina_id", "bimestre_id")
        .annotate(total=Sum("valor"))
        .filter(total__gt=limite)
        .exists()
    )
