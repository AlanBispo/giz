from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError

from contas.models import Usuario
from escolas.models import Bimestre, Disciplina, Escola, Turma
from notas.selectors import maior_nota_da_publicacao

from .models import Publicacao
from .selectors import (
    bloquear_publicacao_docente, publicacoes_do_periodo, somar_atividades, vinculos_do_professor,
)


class PublicacaoDesatualizada(Exception):
    pass


def validar_periodo_docente(
    *, professor: Usuario, turma: Turma, disciplina: Disciplina, bimestre: Bimestre
) -> None:
    if not vinculos_do_professor(professor=professor).filter(turma=turma, disciplina=disciplina).exists():
        raise PermissionDenied("Você não leciona essa disciplina nessa turma.")
    if bimestre.ano_letivo_id != turma.ano_letivo_id:
        raise ValidationError({"bimestre": "Selecione um bimestre do ano letivo da turma."})


@transaction.atomic
def salvar_publicacao(
    *, professor: Usuario, dados: dict, publicacao_id: int | None = None, versao: int | None = None
) -> Publicacao:
    escola = Escola.objects.select_for_update().get()
    publicacao = (
        Publicacao()
        if publicacao_id is None
        else bloquear_publicacao_docente(professor=professor, publicacao_id=publicacao_id)
    )
    if publicacao_id is not None and publicacao.versao != versao:
        raise PublicacaoDesatualizada
    campos_contexto = ("turma_id", "disciplina_id", "bimestre_id", "tipo")
    contexto_anterior = tuple(getattr(publicacao, campo) for campo in campos_contexto)
    era_prova = publicacao.tipo == Publicacao.Tipo.PROVA
    valor_anterior = publicacao.valor
    for campo, valor in dados.items():
        setattr(publicacao, campo, valor)

    turma, disciplina, bimestre = publicacao.turma, publicacao.disciplina, publicacao.bimestre
    validar_periodo_docente(professor=professor, turma=turma, disciplina=disciplina, bimestre=bimestre)
    outras = publicacoes_do_periodo(turma=turma, disciplina=disciplina, bimestre=bimestre).exclude(
        pk=publicacao.pk,
    )
    if publicacao.tipo == Publicacao.Tipo.PROVA:
        if outras.filter(tipo=Publicacao.Tipo.PROVA).exists():
            raise ValidationError({"tipo": "Já existe uma prova para essa turma, disciplina e bimestre."})
        publicacao.valor = valor_anterior if era_prova else escola.pontos_prova
    else:
        if publicacao.valor is None or (era_prova and "valor" not in dados):
            raise ValidationError({"valor": "Informe o valor da atividade."})
        saldo = escola.pontos_atividades - somar_atividades(publicacoes=outras)
        if publicacao.valor > saldo:
            raise ValidationError({"valor": "O valor excede o saldo de pontos de atividades do bimestre."})
    if publicacao_id is not None:
        maior_nota = maior_nota_da_publicacao(publicacao_id=publicacao_id)
        if maior_nota is not None:
            if contexto_anterior != tuple(getattr(publicacao, campo) for campo in campos_contexto):
                raise ValidationError({
                    "non_field_errors": "Turma, disciplina, bimestre e tipo não podem mudar após o lançamento de notas."
                })
            if publicacao.valor < maior_nota:
                raise ValidationError({"valor": "O valor não pode ficar abaixo de uma nota lançada."})
        publicacao.versao += 1
    publicacao.save()
    return publicacao


@transaction.atomic
def excluir_publicacao(*, professor: Usuario, publicacao_id: int, versao: int) -> None:
    Escola.objects.select_for_update().get()
    publicacao = bloquear_publicacao_docente(professor=professor, publicacao_id=publicacao_id)
    if publicacao.versao != versao:
        raise PublicacaoDesatualizada
    try:
        publicacao.delete()
    except ProtectedError as erro:
        raise ValidationError({
            "non_field_errors": "Uma publicação com notas lançadas não pode ser excluída."
        }) from erro


@transaction.atomic
def consultar_saldo(
    *, professor: Usuario, turma: Turma, disciplina: Disciplina, bimestre: Bimestre
) -> dict[str, Decimal]:
    validar_periodo_docente(professor=professor, turma=turma, disciplina=disciplina, bimestre=bimestre)
    escola = Escola.objects.select_for_update().get()
    total = somar_atividades(publicacoes=publicacoes_do_periodo(
        turma=turma, disciplina=disciplina, bimestre=bimestre
    ))
    return {"saldo": escola.pontos_atividades - total, "pontos_prova": escola.pontos_prova}
