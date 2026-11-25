from contas.models import Usuario
from escolas.models import Escola, Turma

from .selectors import totais_por_bimestre


def consultar_boletim(*, usuario: Usuario, turma: Turma | None = None) -> dict:
    media_minima = Escola.objects.get().media_minima
    linhas = []
    for total in totais_por_bimestre(usuario=usuario, turma=turma):
        nome = f"{total['primeiro_nome']} {total['sobrenome']}".strip()
        linhas.append({
            **total,
            "aluno": nome or total["usuario"],
            "situacao": "aprovado" if total["nota"] >= media_minima else "abaixo_da_media",
        })
    return {"media_minima": media_minima, "linhas": linhas}
