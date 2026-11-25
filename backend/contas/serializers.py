from rest_framework import serializers

from .models import Usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    senha = serializers.CharField(max_length=4096, trim_whitespace=False, write_only=True)


class UsuarioSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "nome", "email", "perfil"]

    def get_nome(self, usuario: Usuario) -> str:
        return usuario.get_full_name() or usuario.get_username()
