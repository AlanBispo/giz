from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

from django.db import connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from atividades.models import Publicacao
from atividades.services import PublicacaoDesatualizada, salvar_publicacao
from contas.models import Usuario
from escolas.models import AnoLetivo, Bimestre, Disciplina, Escola, Matricula, Turma, VinculoDocente

from .models import Nota
from .services import LancamentoDesatualizado, salvar_lancamento


class NotasTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        Escola.objects.create(nome="Escola Giz")
        ano = AnoLetivo.objects.create(ano=2027)
        cls.bimestre = Bimestre.objects.create(ano_letivo=ano, numero=1)
        cls.segundo_bimestre = Bimestre.objects.create(ano_letivo=ano, numero=2)
        cls.turma = Turma.objects.create(ano_letivo=ano, nome="7º A")
        cls.outra_turma = Turma.objects.create(ano_letivo=ano, nome="7º B")
        disciplina = Disciplina.objects.create(nome="História")
        cls.professor = Usuario.objects.create_user(username="professor", perfil=Usuario.Perfil.PROFESSOR)
        cls.outro_professor = Usuario.objects.create_user(
            username="outro-professor", perfil=Usuario.Perfil.PROFESSOR,
        )
        cls.aluno = Usuario.objects.create_user(username="aluno", first_name="Alex")
        cls.segundo_aluno = Usuario.objects.create_user(username="segundo-aluno", first_name="Cris")
        cls.aluno_externo = Usuario.objects.create_user(username="aluno-externo", first_name="Sam")
        cls.coordenacao = Usuario.objects.create_user(username="coordenacao", perfil=Usuario.Perfil.COORDENACAO)
        cls.diretoria = Usuario.objects.create_user(username="diretoria", perfil=Usuario.Perfil.DIRETORIA)
        VinculoDocente.objects.create(professor=cls.professor, turma=cls.turma, disciplina=disciplina)
        VinculoDocente.objects.create(
            professor=cls.outro_professor, turma=cls.outra_turma, disciplina=disciplina,
        )
        cls.matricula = Matricula.objects.create(aluno=cls.aluno, turma=cls.turma)
        cls.segunda_matricula = Matricula.objects.create(aluno=cls.segundo_aluno, turma=cls.turma)
        cls.matricula_externa = Matricula.objects.create(aluno=cls.aluno_externo, turma=cls.outra_turma)
        cls.publicacao = Publicacao.objects.create(
            turma=cls.turma, disciplina=disciplina, bimestre=cls.bimestre, titulo="Pesquisa",
            data=date(2027, 3, 10), tipo=Publicacao.Tipo.ATIVIDADE, valor=3,
        )

    def setUp(self) -> None:
        self.api = APIClient()
        self.api.force_login(self.professor)
        self.rota = reverse("nota-lancamento", args=[self.publicacao.pk])

    def _salvar(self, *notas: tuple[Matricula, str], versao: int = 1):
        return self.api.patch(self.rota, {
            "versao": versao,
            "notas": [{"matricula": matricula.pk, "valor": valor} for matricula, valor in notas],
        }, format="json")

    def test_folha_exibe_turma_inteira_e_aceita_zero_e_valor_maximo(self) -> None:
        resposta = self.api.get(self.rota)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("no-store", resposta.headers["Cache-Control"])
        self.assertEqual(resposta.json()["alunos"], [
            {"matricula": self.matricula.pk, "nome": "Alex", "valor": None},
            {"matricula": self.segunda_matricula.pk, "nome": "Cris", "valor": None},
        ])

        gravadas = self._salvar((self.matricula, "0.00"), (self.segunda_matricula, "3.00"))
        self.assertEqual(gravadas.status_code, 200, gravadas.json())
        self.assertEqual([aluno["valor"] for aluno in gravadas.json()["alunos"]], ["0.00", "3.00"])
        versao = gravadas.json()["publicacao"]["versao"]
        corrigida = self._salvar((self.matricula, "1.75"), versao=versao)
        self.assertEqual(corrigida.status_code, 200)
        self.assertEqual(Nota.objects.count(), 2)
        self.assertEqual([aluno["valor"] for aluno in corrigida.json()["alunos"]], ["1.75", "3.00"])

    def test_professor_lanca_nota_de_prova(self) -> None:
        prova = Publicacao.objects.create(
            turma=self.turma, disciplina=self.publicacao.disciplina, bimestre=self.bimestre,
            titulo="Prova", data=date(2027, 3, 15), tipo=Publicacao.Tipo.PROVA, valor=5,
        )
        self.rota = reverse("nota-lancamento", args=[prova.pk])
        resposta = self._salvar((self.matricula, "5.00"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["publicacao"]["tipo"], "prova")
        self.assertEqual(resposta.json()["alunos"][0]["valor"], "5.00")

    def test_lote_invalido_nao_grava_nenhuma_nota(self) -> None:
        for notas in (
            ((self.matricula, "1.00"), (self.segunda_matricula, "3.01")),
            ((self.matricula, "-0.01"),),
            ((self.matricula, "1.00"), (self.matricula, "2.00")),
            ((self.matricula_externa, "1.00"),),
        ):
            with self.subTest(notas=notas):
                self.assertEqual(self._salvar(*notas).status_code, 400)
                self.assertFalse(Nota.objects.exists())

    def test_leitura_por_perfil_respeita_a_privacidade_do_aluno(self) -> None:
        self.assertEqual(self._salvar((self.matricula, "1.50"), (self.segunda_matricula, "3.00")).status_code, 200)
        lista = reverse("nota-list")
        self.assertEqual(self.api.get(lista).status_code, 403)
        self.api.force_login(self.outro_professor)
        self.assertEqual(self.api.get(self.rota).status_code, 404)
        self.assertEqual(self._salvar((self.matricula, "1.00")).status_code, 404)
        self.api.force_login(self.aluno)
        self.assertEqual([nota["valor"] for nota in self.api.get(lista).json()], ["1.50"])
        self.assertEqual(self.api.get(self.rota).status_code, 403)
        self.assertEqual(self._salvar((self.matricula, "2.00")).status_code, 403)
        self.api.force_login(self.aluno_externo)
        self.assertEqual(self.api.get(lista).json(), [])

        for gestor in (self.coordenacao, self.diretoria):
            self.api.force_login(gestor)
            notas = self.api.get(lista).json()
            self.assertEqual([nota["aluno"] for nota in notas], ["Alex", "Cris"])
            self.assertEqual([nota["matricula"] for nota in notas], [
                self.matricula.pk, self.segunda_matricula.pk,
            ])
            self.assertEqual(self._salvar((self.matricula, "2.00")).status_code, 403)

        self.api.logout()
        self.assertEqual(self.api.get(lista).status_code, 403)

    def test_versao_antiga_nao_sobrescreve_notas(self) -> None:
        gravadas = self._salvar((self.matricula, "2.00"))
        self.assertEqual(gravadas.status_code, 200)
        self.assertEqual(self._salvar((self.matricula, "1.00")).status_code, 409)
        self.assertEqual(str(Nota.objects.get().valor), "2.00")

    def test_publicacao_com_nota_preserva_periodo_valor_e_registro(self) -> None:
        gravadas = self._salvar((self.matricula, "2.00"))
        self.assertEqual(gravadas.status_code, 200)
        versao = gravadas.json()["publicacao"]["versao"]
        rota = reverse("publicacao-detail", args=[self.publicacao.pk])
        self.assertEqual(self.api.delete(rota, {"versao": versao}, format="json").status_code, 400)
        for dados in ({"valor": "1.99"}, {"bimestre": self.segundo_bimestre.pk}, {"tipo": "prova"}):
            resposta = self.api.patch(rota, {**dados, "versao": versao}, format="json")
            self.assertEqual(resposta.status_code, 400, resposta.json())
        resposta = self.api.patch(
            rota, {"valor": "2.00", "titulo": "Pesquisa revisada", "versao": versao}, format="json",
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(str(Nota.objects.get().valor), "2.00")

    def test_lancamento_exige_csrf(self) -> None:
        self.api = APIClient(enforce_csrf_checks=True)
        self.api.force_login(self.professor)
        self.assertEqual(self._salvar((self.matricula, "2.00")).status_code, 403)
        token = self.api.get(reverse("csrf")).json()["csrfToken"]
        resposta = self.api.patch(self.rota, {
            "versao": 1, "notas": [{"matricula": self.matricula.pk, "valor": "2.00"}],
        }, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(resposta.status_code, 200)


class NotasConcorrentesTest(TransactionTestCase):
    def test_nota_e_reducao_do_valor_nao_podem_gravar_a_mesma_versao(self) -> None:
        Escola.objects.create(nome="Giz")
        ano = AnoLetivo.objects.create(ano=2027)
        bimestre = Bimestre.objects.create(ano_letivo=ano, numero=1)
        turma = Turma.objects.create(ano_letivo=ano, nome="7º A")
        disciplina = Disciplina.objects.create(nome="História")
        professor = Usuario.objects.create_user(username="professor", perfil=Usuario.Perfil.PROFESSOR)
        aluno = Usuario.objects.create_user(username="aluno")
        VinculoDocente.objects.create(professor=professor, turma=turma, disciplina=disciplina)
        matricula = Matricula.objects.create(aluno=aluno, turma=turma)
        publicacao = Publicacao.objects.create(
            turma=turma, disciplina=disciplina, bimestre=bimestre, titulo="Pesquisa",
            data=date(2027, 3, 10), tipo=Publicacao.Tipo.ATIVIDADE, valor=3,
        )
        inicio = Barrier(2, timeout=5)

        def gravar(operacao: str) -> bool:
            try:
                inicio.wait()
                if operacao == "nota":
                    salvar_lancamento(
                        professor=professor, publicacao_id=publicacao.pk, versao=1,
                        notas=[{"matricula": matricula.pk, "valor": Decimal("2.00")}],
                    )
                else:
                    salvar_publicacao(
                        professor=professor, publicacao_id=publicacao.pk, versao=1,
                        dados={"valor": Decimal("1.00")},
                    )
                return True
            except (LancamentoDesatualizado, PublicacaoDesatualizada):
                return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            nota_gravada, valor_reduzido = executor.map(gravar, ("nota", "reducao"), timeout=20)
        self.assertNotEqual(nota_gravada, valor_reduzido)
        publicacao.refresh_from_db()
        if nota_gravada:
            self.assertEqual(Nota.objects.get().valor, Decimal("2.00"))
            self.assertEqual(publicacao.valor, Decimal("3.00"))
        else:
            self.assertFalse(Nota.objects.exists())
            self.assertEqual(publicacao.valor, Decimal("1.00"))
