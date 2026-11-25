from collections.abc import Mapping
from hashlib import sha256

from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView


class LoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request: Request, view: APIView) -> str | None:
        dados = request.data
        email = dados.get("email") if isinstance(dados, Mapping) else None
        if not isinstance(email, str):
            return None

        email = email.strip().lower()
        if not email or len(email) > 254:
            return None

        origem = self.get_ident(request)
        chave = sha256(f"{origem}\0{email}".encode(errors="replace")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": chave}
