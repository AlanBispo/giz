from django.db import models


class Nota(models.Model):
    publicacao = models.ForeignKey("atividades.Publicacao", on_delete=models.PROTECT)
    matricula = models.ForeignKey("escolas.Matricula", on_delete=models.PROTECT)
    valor = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["publicacao", "matricula"], name="nota_unica_por_publicacao_matricula",
            ),
            models.CheckConstraint(condition=models.Q(valor__gte=0), name="nota_nao_negativa"),
        ]
