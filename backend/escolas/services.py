from collections.abc import Mapping
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from atividades.selectors import ha_periodo_acima_do_limite
from contas.models import Usuario
from contas.selectors import buscar_usuario_por_email

from .models import Disciplina, Escola, Matricula, Turma, VinculoDocente
from .selectors import listar_pessoas_escolares


def cadastrar_pessoa(*, nome: str, email: str, perfil: str, senha: str) -> Usuario:
    if perfil not in (Usuario.Perfil.ALUNO, Usuario.Perfil.PROFESSOR):
        raise ValidationError({"perfil": "Selecione o perfil aluno ou professor."})
    if buscar_usuario_por_email(email=email) is not None:
        raise ValidationError({"email": "Já existe um usuário com este e-mail."})
    usuario = Usuario(
        username=uuid4().hex,
        first_name=nome,
        email=Usuario.objects.normalize_email(email),
        perfil=perfil,
    )
    try:
        validate_password(senha, usuario)
    except ValidationError as erro:
        raise ValidationError({"senha": erro.messages}) from erro

    usuario.set_password(senha)
    usuario.save()
    return usuario


def vincular_professor(
    *, professor: Usuario, turma: Turma, disciplina: Disciplina
) -> VinculoDocente:
    if not listar_pessoas_escolares().filter(pk=professor.pk, perfil=Usuario.Perfil.PROFESSOR).exists():
        raise ValidationError({"professor": "Selecione um professor."})
    return VinculoDocente.objects.create(professor=professor, turma=turma, disciplina=disciplina)


def matricular_aluno(*, aluno: Usuario, turma: Turma) -> Matricula:
    if not listar_pessoas_escolares().filter(pk=aluno.pk, perfil=Usuario.Perfil.ALUNO).exists():
        raise ValidationError({"aluno": "Selecione um aluno."})
    return Matricula.objects.create(aluno=aluno, turma=turma)


@transaction.atomic
def atualizar_regras(*, alteracoes: Mapping[str, Decimal]) -> Escola:
    escola = Escola.objects.select_for_update().get()
    limite = alteracoes.get("pontos_atividades", escola.pontos_atividades)
    if limite < escola.pontos_atividades and ha_periodo_acima_do_limite(limite=limite):
        raise ValidationError({
            "pontos_atividades": "Já foram distribuídos mais pontos de atividades em pelo menos um bimestre."
        })
    for campo, valor in alteracoes.items():
        setattr(escola, campo, valor)
    if alteracoes:
        escola.save(update_fields=alteracoes.keys())
    return escola
