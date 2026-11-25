from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, UsuarioSerializer
from .services import encerrar_sessao, iniciar_sessao
from .throttles import LoginThrottle


@method_decorator(never_cache, name="dispatch")
class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request) -> Response:
        entrada = LoginSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario = iniciar_sessao(request=request, **entrada.validated_data)
        if usuario is None:
            return Response(
                {"detail": "E-mail ou senha inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(UsuarioSerializer(usuario).data)


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        encerrar_sessao(request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(never_cache, name="dispatch")
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UsuarioSerializer(request.user).data)
