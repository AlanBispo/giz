from django.contrib.sessions.middleware import SessionMiddleware
from django.db import transaction
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.urls import reverse


class SessaoMiddleware(SessionMiddleware):
    async_capable = False

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        if request.method != "POST" or request.path != reverse("login"):
            return super().__call__(request)

        with transaction.atomic():
            resposta = super().__call__(request)
            if resposta.status_code >= 400:
                transaction.set_rollback(True)
            return resposta
