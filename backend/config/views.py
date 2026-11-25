import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import verificar_banco

logger = logging.getLogger(__name__)


class SaudeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    def get(self, request: Request) -> Response:
        try:
            verificar_banco()
        except DatabaseError:
            logger.warning("Banco indisponível na verificação de saúde.", exc_info=True)
            return Response(
                {"status": "indisponivel"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"status": "ok"})
