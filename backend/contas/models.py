from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class PerfilUsuario(models.TextChoices):
    ALUNO = "aluno", "Aluno"
    PROFESSOR = "professor", "Professor"
    COORDENACAO = "coordenacao", "Coordenação"
    DIRETORIA = "diretoria", "Diretoria"


class Usuario(AbstractUser):
    Perfil = PerfilUsuario
    perfil = models.CharField(max_length=11, choices=Perfil.choices, default=Perfil.ALUNO)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(perfil__in=PerfilUsuario.values),
                name="contas_usuario_perfil_valido",
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="contas_usuario_email_unico",
            ),
        ]
