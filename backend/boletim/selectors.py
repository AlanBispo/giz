from django.db.models import F, Q, QuerySet, Sum

from atividades.models import Publicacao
from contas.models import Usuario
from escolas.models import Turma
from notas.selectors import notas_visiveis


def totais_por_bimestre(*, usuario: Usuario, turma: Turma | None) -> QuerySet:
    notas = notas_visiveis(usuario=usuario)
    if turma is not None:
        notas = notas.filter(matricula__turma=turma)

    return (
        notas.values(
            "matricula_id",
            turma=F("matricula__turma__nome"),
            ano=F("publicacao__bimestre__ano_letivo__ano"),
            disciplina=F("publicacao__disciplina__nome"),
            bimestre=F("publicacao__bimestre__numero"),
            primeiro_nome=F("matricula__aluno__first_name"),
            sobrenome=F("matricula__aluno__last_name"),
            usuario=F("matricula__aluno__username"),
        )
        .annotate(
            atividades=Sum("valor", filter=Q(publicacao__tipo=Publicacao.Tipo.ATIVIDADE)),
            prova=Sum("valor", filter=Q(publicacao__tipo=Publicacao.Tipo.PROVA)),
            nota=Sum("valor"),
        )
        .order_by("-ano", "turma", "primeiro_nome", "sobrenome", "matricula_id", "disciplina", "bimestre")
    )
