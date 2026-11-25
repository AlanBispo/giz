from rest_framework import serializers

from contas.models import Usuario
from contas.serializers import UsuarioSerializer
from contas.validators import LIMITE_SENHA, validar_email_normalizado

from .models import AnoLetivo, Bimestre, Disciplina, Escola, Matricula, Turma, VinculoDocente


class EscolaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escola
        fields = ("nome", "media_minima", "pontos_atividades", "pontos_prova")
        read_only_fields = ("nome",)


class PessoaSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254, validators=[validar_email_normalizado])
    perfil = serializers.ChoiceField(choices=Usuario.Perfil.choices)
    senha = serializers.CharField(max_length=LIMITE_SENHA, trim_whitespace=False, write_only=True)

    def to_representation(self, instance: Usuario) -> dict:
        return UsuarioSerializer(instance).data


class AnoLetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnoLetivo
        fields = ("id", "ano")


class BimestreSerializer(serializers.ModelSerializer):
    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = Bimestre
        fields = ("id", "ano_letivo", "numero", "ano")


class TurmaSerializer(serializers.ModelSerializer):
    ano = serializers.IntegerField(source="ano_letivo.ano", read_only=True)

    class Meta:
        model = Turma
        fields = ("id", "ano_letivo", "nome", "ano")


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = ("id", "nome")


class VinculoDocenteSerializer(serializers.ModelSerializer):
    nome_professor = serializers.CharField(source="professor.nome_de_exibicao", read_only=True)
    nome_turma = serializers.StringRelatedField(source="turma")
    nome_disciplina = serializers.StringRelatedField(source="disciplina")

    class Meta:
        model = VinculoDocente
        fields = (
            "id", "professor", "turma", "disciplina", "nome_professor", "nome_turma", "nome_disciplina"
        )


class MatriculaSerializer(serializers.ModelSerializer):
    nome_aluno = serializers.CharField(source="aluno.nome_de_exibicao", read_only=True)
    nome_turma = serializers.StringRelatedField(source="turma")

    class Meta:
        model = Matricula
        fields = ("id", "aluno", "turma", "nome_aluno", "nome_turma")
