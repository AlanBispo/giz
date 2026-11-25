from django.db.models import QuerySet

from contas.models import Usuario


def listar_pessoas_escolares() -> QuerySet[Usuario]:
    return Usuario.objects.filter(
        perfil__in=(Usuario.Perfil.ALUNO, Usuario.Perfil.PROFESSOR),
        is_staff=False,
        is_superuser=False,
    ).order_by("first_name", "last_name", "pk")
