from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Escola(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    nome = models.CharField(max_length=150)
    media_minima = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    pontos_atividades = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    pontos_prova = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.0"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="escola_unica"),
            models.CheckConstraint(
                condition=models.Q(
                    media_minima__gte=0, pontos_atividades__gte=0, pontos_prova__gte=0
                ),
                name="escola_regras_nao_negativas",
            ),
        ]

    def __str__(self) -> str:
        return self.nome


class AnoLetivo(models.Model):
    ano = models.PositiveSmallIntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(9999)]
    )

    class Meta:
        ordering = ["-ano"]
        verbose_name_plural = "anos letivos"

    def __str__(self) -> str:
        return str(self.ano)


class Bimestre(models.Model):
    ano_letivo = models.ForeignKey(AnoLetivo, on_delete=models.PROTECT)
    numero = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    class Meta:
        ordering = ["-ano_letivo__ano", "numero"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(numero__range=(1, 4)), name="bimestre_numero_valido"
            ),
            models.UniqueConstraint(
                fields=["ano_letivo", "numero"], name="bimestre_unico_por_ano"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.numero}º bimestre de {self.ano_letivo}"


class Turma(models.Model):
    ano_letivo = models.ForeignKey(AnoLetivo, on_delete=models.PROTECT)
    nome = models.CharField(max_length=100)

    class Meta:
        ordering = ["-ano_letivo__ano", "nome", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["ano_letivo", "nome"], name="turma_unica_por_ano"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ano_letivo})"


class Disciplina(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class VinculoDocente(models.Model):
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["professor", "turma", "disciplina"], name="vinculo_docente_unico"
            ),
        ]


class Matricula(models.Model):
    aluno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["aluno", "turma"], name="matricula_unica_por_turma"),
        ]
