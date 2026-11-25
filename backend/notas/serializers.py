from decimal import Decimal

from rest_framework import serializers

from atividades.models import Publicacao

from .models import Nota


class PublicacaoResumoSerializer(serializers.ModelSerializer):
    nome_turma = serializers.StringRelatedField(source="turma")
    nome_disciplina = serializers.CharField(source="disciplina.nome")
    numero_bimestre = serializers.IntegerField(source="bimestre.numero")

    class Meta:
        model = Publicacao
        fields = (
            "id", "titulo", "tipo", "data", "valor", "versao", "nome_turma",
            "nome_disciplina", "numero_bimestre",
        )


class AlunoLancamentoSerializer(serializers.Serializer):
    matricula = serializers.IntegerField(source="id")
    nome = serializers.CharField(source="aluno.nome_de_exibicao")
    valor = serializers.DecimalField(
        source="valor_nota", max_digits=5, decimal_places=2, allow_null=True,
    )


class LancamentoSerializer(serializers.Serializer):
    publicacao = PublicacaoResumoSerializer()
    alunos = AlunoLancamentoSerializer(many=True)


class NotaInformadaSerializer(serializers.Serializer):
    matricula = serializers.IntegerField(min_value=1)
    valor = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0.00"))


class AlteracaoLancamentoSerializer(serializers.Serializer):
    versao = serializers.IntegerField(min_value=1)
    notas = NotaInformadaSerializer(many=True, allow_empty=False)


class NotaConsultaSerializer(serializers.ModelSerializer):
    aluno = serializers.CharField(source="matricula.aluno.nome_de_exibicao")
    matricula = serializers.IntegerField(source="matricula_id")
    publicacao = PublicacaoResumoSerializer()

    class Meta:
        model = Nota
        fields = ("id", "aluno", "matricula", "publicacao", "valor")
