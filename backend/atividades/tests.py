from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

from django.core.exceptions import ValidationError
from django.db import connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from contas.models import Usuario
from escolas.models import AnoLetivo, Bimestre, Disciplina, Escola, Matricula, Turma, VinculoDocente

from .models import Publicacao
from .services import salvar_publicacao


class PublicacoesTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        Escola.objects.create(nome="Giz")
        ano = AnoLetivo.objects.create(ano=2027)
        outro_ano = AnoLetivo.objects.create(ano=2028)
        cls.bimestre = Bimestre.objects.create(ano_letivo=ano, numero=1)
        cls.segundo_bimestre = Bimestre.objects.create(ano_letivo=ano, numero=2)
        cls.outro_bimestre = Bimestre.objects.create(ano_letivo=outro_ano, numero=1)
        cls.turma = Turma.objects.create(ano_letivo=ano, nome="7º A")
        cls.outra_turma = Turma.objects.create(ano_letivo=ano, nome="7º B")
        cls.disciplina = Disciplina.objects.create(nome="História")
        cls.outra_disciplina = Disciplina.objects.create(nome="Matemática")
        cls.professor = Usuario.objects.create_user(username="professor", perfil=Usuario.Perfil.PROFESSOR)
        cls.aluno = Usuario.objects.create_user(username="aluno")
        cls.diretora = Usuario.objects.create_user(username="diretora", perfil=Usuario.Perfil.DIRETORIA)
        VinculoDocente.objects.create(professor=cls.professor, turma=cls.turma, disciplina=cls.disciplina)
        Matricula.objects.create(aluno=cls.aluno, turma=cls.turma)

    def setUp(self) -> None:
        self.api = APIClient()
        self.api.force_login(self.professor)
        self.periodo = {
            "turma": self.turma.pk, "disciplina": self.disciplina.pk, "bimestre": self.bimestre.pk,
        }
        self.dados = {
            **self.periodo, "titulo": "Pesquisa", "descricao": "Pesquisar a história da cidade.",
            "tipo": "atividade", "data": "2027-03-10", "valor": "3.00",
        }

    def _criar(self, **alteracoes: object) -> dict:
        resposta = self.api.post(
            reverse("publicacao-list"), {**self.dados, **alteracoes}, format="json",
        )
        self.assertEqual(resposta.status_code, 201, resposta.json())
        return resposta.json()

    def test_professor_distribui_pontos_edita_e_exclui(self) -> None:
        atividade = self._criar()
        outra = self._criar(valor="2.00")
        saldo = reverse("saldo-atividades")
        self.assertEqual(self.api.get(saldo, self.periodo).json()["saldo"], "0.00")
        erro = self.api.post(reverse("publicacao-list"), {**self.dados, "valor": "0.01"}, format="json")
        self.assertEqual(erro.status_code, 400)
        rota = reverse("publicacao-detail", args=[atividade["id"]])
        self.assertEqual(self.api.patch(
            rota, {"valor": "3.01", "versao": atividade["versao"]}, format="json",
        ).status_code, 400)
        self.assertEqual(self.api.patch(
            rota, {"valor": "2.50", "versao": atividade["versao"]}, format="json",
        ).status_code, 200)
        self.assertEqual(self.api.get(saldo, self.periodo).json()["saldo"], "0.50")
        self.assertEqual(self.api.delete(
            reverse("publicacao-detail", args=[outra["id"]]), {"versao": outra["versao"]}, format="json",
        ).status_code, 204)
        self.assertEqual(self.api.get(saldo, self.periodo).json()["saldo"], "2.50")
        self._criar(valor="5.00", bimestre=self.segundo_bimestre.pk)

    def test_prova_unica_recebe_valor_da_escola_e_preserva_publicacao(self) -> None:
        prova = self._criar(tipo="prova", valor="1.00")
        self.assertEqual(prova["valor"], "5.00")
        duplicada = self.api.post(reverse("publicacao-list"), {**self.dados, "tipo": "prova"}, format="json")
        self.assertEqual(duplicada.status_code, 400)
        self.assertEqual(self.api.get(reverse("saldo-atividades"), self.periodo).json()["saldo"], "5.00")

        self.api.force_login(self.diretora)
        self.assertEqual(
            self.api.patch(reverse("regras-escola"), {"pontos_prova": "7.00"}, format="json").status_code,
            200,
        )
        self.api.force_login(self.professor)
        edicao = self.api.patch(
            reverse("publicacao-detail", args=[prova["id"]]),
            {"titulo": "Prova editada", "valor": "2.00", "versao": prova["versao"]},
            format="json",
        )
        self.assertEqual(edicao.json()["valor"], "5.00")
        mudanca_de_periodo = self.api.patch(
            reverse("publicacao-detail", args=[prova["id"]]),
            {"bimestre": self.segundo_bimestre.pk, "versao": edicao.json()["versao"]},
            format="json",
        )
        self.assertEqual(mudanca_de_periodo.status_code, 200)
        self.assertEqual(mudanca_de_periodo.json()["valor"], "5.00")
        self.assertEqual(self._criar(tipo="prova")["valor"], "7.00")

    def test_permissoes_respeitam_matricula_e_par_turma_disciplina(self) -> None:
        atividade = self._criar()
        Publicacao.objects.create(
            turma=self.turma, disciplina=self.outra_disciplina, bimestre=self.bimestre,
            titulo="Da turma", data=date(2027, 3, 10), tipo=Publicacao.Tipo.PROVA, valor=5,
        )
        oculta = Publicacao.objects.create(
            turma=self.outra_turma, disciplina=self.disciplina, bimestre=self.bimestre,
            titulo="De outra turma", data=date(2027, 3, 10), tipo=Publicacao.Tipo.ATIVIDADE, valor=1,
        )
        lista = reverse("publicacao-list")
        self.assertEqual([item["id"] for item in self.api.get(lista).json()], [atividade["id"]])
        self.assertEqual(self.api.get(reverse("publicacao-detail", args=[oculta.pk])).status_code, 404)
        edicao = self.api.patch(
            reverse("publicacao-detail", args=[atividade["id"]]),
            {"disciplina": self.outra_disciplina.pk, "versao": atividade["versao"]},
            format="json",
        )
        self.assertEqual(edicao.status_code, 403)
        self.assertEqual(self.api.post(
            lista, {**self.dados, "bimestre": self.outro_bimestre.pk}, format="json",
        ).status_code, 400)
        contexto = self.api.get(reverse("contexto-atividades")).json()
        self.assertEqual(len(contexto), 1)
        self.assertEqual([item["id"] for item in contexto[0]["bimestres"]], [
            self.bimestre.pk, self.segundo_bimestre.pk,
        ])

        self.api.force_login(self.aluno)
        self.assertEqual({item["titulo"] for item in self.api.get(lista).json()}, {"Pesquisa", "Da turma"})
        self.assertEqual(self.api.get(reverse("publicacao-detail", args=[oculta.pk])).status_code, 404)
        self.assertEqual(self.api.get(reverse("contexto-atividades")).status_code, 403)
        self.assertEqual(self.api.post(lista, self.dados, format="json").status_code, 403)
        self.assertEqual(self.api.delete(reverse("publicacao-detail", args=[atividade["id"]])).status_code, 403)
        self.api.force_login(self.diretora)
        self.assertEqual(self.api.get(lista).status_code, 403)

    def test_diretoria_nao_pode_reduzir_limite_abaixo_dos_pontos_distribuidos(self) -> None:
        self._criar(valor="4.00")
        self.api.force_login(self.diretora)
        rota = reverse("regras-escola")
        self.assertEqual(self.api.patch(rota, {"pontos_atividades": "3.99"}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(rota, {"pontos_atividades": "4.00"}, format="json").status_code, 200)

    def test_edicao_e_exclusao_rejeitam_versoes_desatualizadas(self) -> None:
        atividade = self._criar()
        rota = reverse("publicacao-detail", args=[atividade["id"]])
        dados_anteriores = {"versao": atividade["versao"]}
        edicao = self.api.patch(rota, {**dados_anteriores, "tipo": "prova"}, format="json")
        self.assertEqual(edicao.status_code, 200)
        self.assertGreater(edicao.json()["versao"], atividade["versao"])
        self.assertEqual(self.api.patch(
            rota, {**dados_anteriores, "valor": "1.00"}, format="json",
        ).status_code, 409)
        self.assertEqual(self.api.delete(rota, dados_anteriores, format="json").status_code, 409)
        self.assertEqual(self.api.get(rota).json()["tipo"], "prova")
        self.assertEqual(self.api.delete(
            rota, {"versao": edicao.json()["versao"]}, format="json",
        ).status_code, 204)
        self.assertEqual(self.api.patch(
            rota, {**dados_anteriores, "valor": "1.00"}, format="json",
        ).status_code, 404)

    def test_gravacoes_exigem_csrf(self) -> None:
        self.api = APIClient(enforce_csrf_checks=True)
        self.api.force_login(self.professor)
        rota = reverse("publicacao-list")
        self.assertEqual(self.api.post(rota, self.dados, format="json").status_code, 403)
        token = self.api.get(reverse("csrf")).json()["csrfToken"]
        criada = self.api.post(rota, self.dados, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(criada.status_code, 201)
        publicacao = criada.json()
        detalhe = reverse("publicacao-detail", args=[publicacao["id"]])
        dados = {"versao": publicacao["versao"]}
        self.assertEqual(self.api.delete(detalhe, dados, format="json").status_code, 403)
        self.assertEqual(self.api.delete(
            detalhe, dados, format="json", HTTP_X_CSRFTOKEN=token,
        ).status_code, 204)

    def test_excluir_sem_escola_cadastrada_retorna_404(self) -> None:
        Escola.objects.all().delete()
        rota = reverse("publicacao-detail", args=[1])
        self.assertEqual(self.api.delete(rota, {"versao": 1}, format="json").status_code, 404)


class PublicacoesConcorrentesTest(TransactionTestCase):
    def test_duas_gravacoes_nao_ultrapassam_saldo(self) -> None:
        Escola.objects.create(nome="Giz")
        ano = AnoLetivo.objects.create(ano=2027)
        bimestre = Bimestre.objects.create(ano_letivo=ano, numero=1)
        turma = Turma.objects.create(ano_letivo=ano, nome="7º A")
        disciplina = Disciplina.objects.create(nome="História")
        professor = Usuario.objects.create_user(username="professor", perfil=Usuario.Perfil.PROFESSOR)
        VinculoDocente.objects.create(professor=professor, turma=turma, disciplina=disciplina)
        inicio = Barrier(2, timeout=5)

        def gravar(titulo: str) -> bool:
            try:
                inicio.wait()
                salvar_publicacao(professor=professor, dados={
                    "titulo": titulo, "turma": turma, "disciplina": disciplina, "bimestre": bimestre,
                    "data": date(2027, 3, 10), "tipo": Publicacao.Tipo.ATIVIDADE, "valor": Decimal("3.00"),
                })
                return True
            except ValidationError as erro:
                self.assertIn("valor", erro.message_dict)
                return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(gravar, ("Primeira", "Segunda"), timeout=20))
        self.assertCountEqual(resultados, [True, False])
        self.assertEqual(Publicacao.objects.count(), 1)
