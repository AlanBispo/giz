from datetime import timedelta
from unittest.mock import patch

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.cache.backends.locmem import LocMemCache
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Usuario
from .throttles import LoginThrottle


class SessaoTest(TestCase):
    senha = "Senha de teste 2026"

    @classmethod
    def setUpTestData(cls) -> None:
        for perfil in Usuario.Perfil:
            Usuario.objects.create_user(
                username=perfil,
                first_name=perfil.label,
                email=f"{perfil}@example.com",
                password=cls.senha,
                perfil=perfil,
            )

    def setUp(self) -> None:
        self.api = APIClient(enforce_csrf_checks=True)

    def _token_csrf(self) -> str:
        resposta = self.api.get(reverse("csrf"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("csrftoken", resposta.cookies)
        return resposta.json()["csrfToken"]

    def test_login_me_e_logout_para_cada_perfil(self) -> None:
        for perfil in Usuario.Perfil:
            with self.subTest(perfil=perfil):
                self.assertEqual(self.api.get(reverse("me")).status_code, 403)
                token_antes_do_login = self._token_csrf()
                resposta = self.api.post(
                    reverse("login"),
                    {"email": f"{perfil.upper()}@example.com", "senha": self.senha},
                    format="json",
                    HTTP_X_CSRFTOKEN=token_antes_do_login,
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("sessionid", resposta.cookies)
                self.assertNotIn("senha", resposta.json())

                me = self.api.get(reverse("me"))
                self.assertEqual(me.status_code, 200)
                self.assertEqual(me.json(), resposta.json())
                self.assertEqual(me.json()["perfil"], perfil)
                self.assertEqual(me.json()["nome"], perfil.label)

                self.assertEqual(
                    self.api.post(
                        reverse("logout"), HTTP_X_CSRFTOKEN=token_antes_do_login
                    ).status_code,
                    403,
                )
                self.assertEqual(self.api.get(reverse("me")).status_code, 200)
                self.assertEqual(
                    self.api.post(
                        reverse("logout"), HTTP_X_CSRFTOKEN=self._token_csrf()
                    ).status_code,
                    204,
                )
                self.assertEqual(self.api.get(reverse("me")).status_code, 403)

    def test_login_exige_csrf_mesmo_sem_sessao(self) -> None:
        self._token_csrf()
        resposta = self.api.post(
            reverse("login"),
            {"email": "aluno@example.com", "senha": self.senha},
            format="json",
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.api.get(reverse("me")).status_code, 403)

    def test_credenciais_invalidas_nao_revelam_se_a_conta_existe(self) -> None:
        token = self._token_csrf()
        for email in ("aluno@example.com", "inexistente@example.com"):
            with self.subTest(email=email):
                resposta = self.api.post(
                    reverse("login"),
                    {"email": email, "senha": "senha errada"},
                    format="json",
                    HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(resposta.status_code, 400)
                self.assertEqual(resposta.json(), {"detail": "E-mail ou senha inválidos."})
                self.assertNotIn("sessionid", resposta.cookies)

    def test_falha_ao_salvar_sessao_reverte_o_login(self) -> None:
        token = self._token_csrf()
        salvar = SessionStore.save

        def salvar_apenas_na_criacao(sessao: SessionStore, must_create: bool = False) -> None:
            if not must_create:
                raise RuntimeError("Falha ao salvar sessão")
            salvar(sessao, must_create=True)

        with (
            patch.object(SessionStore, "save", salvar_apenas_na_criacao),
            self.assertRaisesMessage(RuntimeError, "Falha ao salvar sessão"),
        ):
            self.api.post(
                reverse("login"),
                {"email": "aluno@example.com", "senha": self.senha},
                format="json",
                HTTP_X_CSRFTOKEN=token,
            )

        self.assertFalse(Session.objects.exists())
        self.assertIsNone(Usuario.objects.get(username="aluno").last_login)

    def test_login_limita_tentativas_sem_bloquear_outra_conta_no_mesmo_proxy(self) -> None:
        token = self._token_csrf()
        cache = LocMemCache("teste-limite-de-login", {})
        with (
            patch.object(LoginThrottle, "cache", cache),
            patch.object(LoginThrottle, "THROTTLE_RATES", {"login": "2/min"}),
        ):
            for email, status_esperado in (
                ("aluno@example.com", 400),
                (" ALUNO@example.com ", 400),
                ("aluno@example.com", 429),
            ):
                resposta = self.api.post(
                    reverse("login"),
                    {"email": email, "senha": "senha errada"},
                    format="json",
                    HTTP_X_CSRFTOKEN=token,
                    REMOTE_ADDR="127.0.0.1",
                )
                self.assertEqual(resposta.status_code, status_esperado)

            resposta = self.api.post(
                reverse("login"),
                {"email": "professor@example.com", "senha": self.senha},
                format="json",
                HTTP_X_CSRFTOKEN=token,
                REMOTE_ADDR="127.0.0.1",
            )
            self.assertEqual(resposta.status_code, 200)

    def test_logout_fecha_sessao_expirada_e_continua_exigindo_csrf(self) -> None:
        resposta = self.api.post(
            reverse("login"),
            {"email": "aluno@example.com", "senha": self.senha},
            format="json",
            HTTP_X_CSRFTOKEN=self._token_csrf(),
        )
        self.assertEqual(resposta.status_code, 200)
        Session.objects.filter(session_key=resposta.cookies["sessionid"].value).update(
            expire_date=timezone.now() - timedelta(seconds=1)
        )

        self.assertEqual(self.api.post(reverse("logout")).status_code, 403)

        resposta = self.api.post(reverse("logout"), HTTP_X_CSRFTOKEN=self._token_csrf())
        self.assertEqual(resposta.status_code, 204)
        self.assertEqual(resposta.cookies["sessionid"]["max-age"], 0)
        self.assertEqual(self.api.get(reverse("me")).status_code, 403)

    def test_banco_rejeita_perfil_fora_dos_quatro_previstos(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.filter(username="aluno").update(perfil="invalido")
