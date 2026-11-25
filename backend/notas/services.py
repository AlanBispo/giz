from decimal import Decimal
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction

from atividades.selectors import bloquear_publicacao_docente
from contas.models import Usuario
from escolas.models import Matricula

from .models import Nota
from .selectors import Lancamento, montar_lancamento


class NotaInformada(TypedDict):
    matricula: int
    valor: Decimal


class LancamentoDesatualizado(Exception):
    pass


@transaction.atomic
def consultar_lancamento(*, professor: Usuario, publicacao_id: int) -> Lancamento:
    publicacao = bloquear_publicacao_docente(professor=professor, publicacao_id=publicacao_id)
    return montar_lancamento(publicacao=publicacao)


@transaction.atomic
def salvar_lancamento(
    *, professor: Usuario, publicacao_id: int, versao: int, notas: list[NotaInformada],
) -> Lancamento:
    publicacao = bloquear_publicacao_docente(professor=professor, publicacao_id=publicacao_id)
    if publicacao.versao != versao:
        raise LancamentoDesatualizado

    matriculas = {nota["matricula"] for nota in notas}
    if len(matriculas) != len(notas):
        raise ValidationError({"notas": "Informe apenas uma nota para cada aluno."})
    if Matricula.objects.filter(pk__in=matriculas, turma_id=publicacao.turma_id).count() != len(matriculas):
        raise ValidationError({"notas": "Selecione apenas alunos matriculados nesta turma."})
    if any(not Decimal("0.00") <= nota["valor"] <= publicacao.valor for nota in notas):
        maximo = str(publicacao.valor).replace(".", ",")
        raise ValidationError({"notas": f"As notas devem estar entre 0 e {maximo}."})

    Nota.objects.bulk_create(
        [Nota(publicacao=publicacao, matricula_id=nota["matricula"], valor=nota["valor"]) for nota in notas],
        update_conflicts=True,
        update_fields=["valor"],
        unique_fields=["publicacao", "matricula"],
    )
    publicacao.versao += 1
    publicacao.save(update_fields=["versao"])
    return montar_lancamento(publicacao=publicacao)
