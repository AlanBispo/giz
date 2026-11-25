from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class SaudeTest(TestCase):
    def test_responde_ok_quando_o_banco_esta_disponivel(self) -> None:
        resposta = self.client.get(reverse("saude"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})

    def test_responde_503_quando_o_banco_esta_indisponivel(self) -> None:
        with (
            patch("config.selectors.connection.cursor", side_effect=OperationalError),
            self.assertLogs("config.views", level="WARNING"),
        ):
            resposta = self.client.get(reverse("saude"))

        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json(), {"status": "indisponivel"})
