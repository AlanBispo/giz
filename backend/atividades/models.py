from django.db import models

from escolas.models import Bimestre, Disciplina, Turma


class Publicacao(models.Model):
    class Tipo(models.TextChoices):
        ATIVIDADE = "atividade", "Atividade"
        PROVA = "prova", "Prova"

    turma = models.ForeignKey(Turma, on_delete=models.PROTECT)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT)
    bimestre = models.ForeignKey(Bimestre, on_delete=models.PROTECT)
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    data = models.DateField()
    tipo = models.CharField(max_length=9, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    versao = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        ordering = ("data", "pk")
        indexes = [models.Index(fields=["turma", "disciplina", "bimestre"], name="publicacao_periodo_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor__gte=0, tipo__in=["atividade", "prova"]),
                name="publicacao_tipo_valor_validos",
            ),
            models.UniqueConstraint(
                fields=["turma", "disciplina", "bimestre"],
                condition=models.Q(tipo="prova"),
                name="publicacao_prova_unica_periodo",
            ),
        ]
