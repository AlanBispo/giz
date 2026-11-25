from rest_framework import serializers

from .models import Usuario
from .validators import LIMITE_SENHA


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    senha = serializers.CharField(max_length=LIMITE_SENHA, trim_whitespace=False, write_only=True)


class UsuarioSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="nome_de_exibicao", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nome", "email", "perfil"]
