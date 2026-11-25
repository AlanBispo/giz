from decimal import Decimal

from rest_framework import serializers

from escolas.models import Bimestre, Disciplina, Turma

from .models import Publicacao


class PeriodoSerializer(serializers.Serializer):
    turma = serializers.PrimaryKeyRelatedField(queryset=Turma.objects.all())
    disciplina = serializers.PrimaryKeyRelatedField(queryset=Disciplina.objects.all())
    bimestre = serializers.PrimaryKeyRelatedField(queryset=Bimestre.objects.all())


class PublicacaoSerializer(serializers.ModelSerializer):
    nome_turma = serializers.StringRelatedField(source="turma")
    nome_disciplina = serializers.CharField(source="disciplina.nome", read_only=True)
    numero_bimestre = serializers.IntegerField(source="bimestre.numero", read_only=True)
    descricao = serializers.CharField(allow_blank=True, required=False, max_length=5000)
    valor = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0.00"), required=False,
    )
    versao = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Publicacao
        fields = (
            "id", "titulo", "descricao", "data", "tipo", "valor", "turma", "disciplina",
            "bimestre", "nome_turma", "nome_disciplina", "numero_bimestre", "versao",
        )
        validators = []


class VersaoSerializer(serializers.Serializer):
    versao = serializers.IntegerField(min_value=1)


class SaldoSerializer(serializers.Serializer):
    saldo = serializers.DecimalField(max_digits=5, decimal_places=2)
    pontos_prova = serializers.DecimalField(max_digits=5, decimal_places=2)


class BimestreResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    numero = serializers.IntegerField()


class ContextoSerializer(serializers.Serializer):
    turma = serializers.IntegerField(source="vinculo.turma_id")
    disciplina = serializers.IntegerField(source="vinculo.disciplina_id")
    nome_turma = serializers.StringRelatedField(source="vinculo.turma")
    nome_disciplina = serializers.CharField(source="vinculo.disciplina.nome")
    bimestres = BimestreResumoSerializer(many=True)
