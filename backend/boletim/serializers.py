from rest_framework import serializers


class LinhaBoletimSerializer(serializers.Serializer):
    matricula = serializers.IntegerField(source="matricula_id")
    aluno = serializers.CharField()
    turma = serializers.CharField()
    ano = serializers.IntegerField()
    disciplina = serializers.CharField()
    bimestre = serializers.IntegerField()
    atividades = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    prova = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    nota = serializers.DecimalField(max_digits=6, decimal_places=2)
    situacao = serializers.CharField()


class BoletimSerializer(serializers.Serializer):
    media_minima = serializers.DecimalField(max_digits=5, decimal_places=2)
    linhas = LinhaBoletimSerializer(many=True)
