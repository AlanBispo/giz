from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from atividades.models import Publicacao
from contas.models import Usuario
from escolas.models import AnoLetivo, Bimestre, Disciplina, Escola, Matricula, Turma
from notas.models import Nota


class BoletimTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        Escola.objects.create(nome="Escola Giz")
        ano = AnoLetivo.objects.create(ano=2027)
        primeiro = Bimestre.objects.create(ano_letivo=ano, numero=1)
        segundo = Bimestre.objects.create(ano_letivo=ano, numero=2)
        cls.turma = Turma.objects.create(ano_letivo=ano, nome="7º A")
        cls.outra_turma = Turma.objects.create(ano_letivo=ano, nome="7º B")
        historia = Disciplina.objects.create(nome="História")
        matematica = Disciplina.objects.create(nome="Matemática")
        cls.aluno = Usuario.objects.create_user(username="alex", first_name="Alex")
        cls.colega = Usuario.objects.create_user(username="cris")
        cls.aluno_sem_nota = Usuario.objects.create_user(username="sem-nota")
        cls.professor = Usuario.objects.create_user(username="professor", perfil=Usuario.Perfil.PROFESSOR)
        cls.coordenacao = Usuario.objects.create_user(username="coord", perfil=Usuario.Perfil.COORDENACAO)
        cls.diretoria = Usuario.objects.create_user(username="diretoria", perfil=Usuario.Perfil.DIRETORIA)
        cls.matricula = Matricula.objects.create(aluno=cls.aluno, turma=cls.turma)
        cls.matricula_colega = Matricula.objects.create(aluno=cls.colega, turma=cls.turma)
        cls.outra_matricula = Matricula.objects.create(aluno=cls.aluno, turma=cls.outra_turma)
        Matricula.objects.create(aluno=cls.aluno_sem_nota, turma=cls.outra_turma)

        def publicar(
            turma: Turma, disciplina: Disciplina, bimestre: Bimestre, titulo: str, valor: str,
            tipo: Publicacao.Tipo = Publicacao.Tipo.ATIVIDADE,
        ) -> Publicacao:
            return Publicacao.objects.create(
                turma=turma, disciplina=disciplina, bimestre=bimestre, titulo=titulo,
                data=date(2027, 2 * bimestre.numero + 1, 1), tipo=tipo, valor=valor,
            )

        atividade = publicar(cls.turma, historia, primeiro, "Pesquisa", "3.00")
        trabalho = publicar(cls.turma, historia, primeiro, "Trabalho", "2.00")
        prova = publicar(cls.turma, historia, primeiro, "Prova", "5.00", Publicacao.Tipo.PROVA)
        publicar(cls.turma, matematica, primeiro, "Projeto", "1.00")
        atividade_segundo = publicar(cls.turma, historia, segundo, "Atividade", "5.00")
        prova_matematica = publicar(cls.turma, matematica, segundo, "Prova", "5.00", Publicacao.Tipo.PROVA)
        atividade_outra = publicar(cls.outra_turma, historia, primeiro, "Atividade", "5.00")
        Nota.objects.bulk_create([
            Nota(publicacao=atividade, matricula=cls.matricula, valor="1.10"),
            Nota(publicacao=trabalho, matricula=cls.matricula, valor="0.90"),
            Nota(publicacao=prova, matricula=cls.matricula, valor="3.00"),
            Nota(publicacao=atividade_segundo, matricula=cls.matricula, valor="0.00"),
            Nota(publicacao=prova_matematica, matricula=cls.matricula, valor="4.99"),
            Nota(publicacao=atividade_outra, matricula=cls.outra_matricula, valor="4.00"),
            Nota(publicacao=atividade, matricula=cls.matricula_colega, valor="3.00"),
            Nota(publicacao=trabalho, matricula=cls.matricula_colega, valor="2.00"),
            Nota(publicacao=prova, matricula=cls.matricula_colega, valor="5.00"),
        ])

    def setUp(self) -> None:
        self.api = APIClient()
        self.rota_aluno = reverse("meu-boletim")
        self.rota_turma = reverse("boletim-da-turma", args=[self.turma.pk])

    def test_aluno_consulta_proprias_notas_separadas_por_turma_disciplina_e_bimestre(self) -> None:
        self.api.force_login(self.aluno)
        resposta = self.api.get(self.rota_aluno, {"aluno": self.colega.pk, "turma": self.turma.pk})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("no-store", resposta.headers["Cache-Control"])
        dados = resposta.json()
        self.assertEqual(dados["media_minima"], "5.00")
        self.assertEqual([
            (linha["matricula"], linha["disciplina"], linha["bimestre"], linha["atividades"],
             linha["prova"], linha["nota"], linha["situacao"])
            for linha in dados["linhas"]
        ], [
            (self.matricula.pk, "História", 1, "2.00", "3.00", "5.00", "aprovado"),
            (self.matricula.pk, "História", 2, "0.00", None, "0.00", "abaixo_da_media"),
            (self.matricula.pk, "Matemática", 2, None, "4.99", "4.99", "abaixo_da_media"),
            (self.outra_matricula.pk, "História", 1, "4.00", None, "4.00", "abaixo_da_media"),
        ])

    def test_gestao_consulta_alunos_da_turma_selecionada(self) -> None:
        for usuario in (self.coordenacao, self.diretoria):
            with self.subTest(perfil=usuario.perfil):
                self.api.force_login(usuario)
                resposta = self.api.get(self.rota_turma)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn("no-store", resposta.headers["Cache-Control"])
                linhas = resposta.json()["linhas"]
                self.assertEqual(len(linhas), 4)
                self.assertEqual({linha["matricula"] for linha in linhas}, {
                    self.matricula.pk, self.matricula_colega.pk,
                })
                [linha_colega] = [linha for linha in linhas if linha["matricula"] == self.matricula_colega.pk]
                self.assertEqual((linha_colega["aluno"], linha_colega["nota"]), ("cris", "10.00"))
                self.assertEqual(self.api.get(self.rota_aluno).status_code, 403)
                self.assertEqual(self.api.get(reverse("boletim-da-turma", args=[0])).status_code, 404)

    def test_rejeita_perfis_sem_acesso_a_cada_rota(self) -> None:
        for rota in (self.rota_aluno, self.rota_turma):
            with self.subTest(rota=rota):
                self.api.logout()
                self.assertEqual(self.api.get(rota).status_code, 403)
                self.api.force_login(self.professor)
                self.assertEqual(self.api.get(rota).status_code, 403)
        self.api.force_login(self.aluno)
        self.assertEqual(self.api.get(self.rota_turma).status_code, 403)

    def test_aluno_sem_lancamentos_recebe_boletim_vazio(self) -> None:
        self.api.force_login(self.aluno_sem_nota)
        resposta = self.api.get(self.rota_aluno)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"media_minima": "5.00", "linhas": []})

    def test_mudanca_nas_regras_atualiza_a_situacao_e_preserva_notas(self) -> None:
        self.api.force_login(self.diretoria)
        [linha_anterior] = [
            linha for linha in self.api.get(self.rota_turma).json()["linhas"]
            if linha["matricula"] == self.matricula.pk
            and linha["disciplina"] == "História" and linha["bimestre"] == 1
        ]
        self.assertEqual(linha_anterior["situacao"], "aprovado")
        notas_anteriores = list(Nota.objects.order_by("pk").values_list("pk", "valor"))
        resposta = self.api.patch(reverse("regras-escola"), {
            "media_minima": "5.01", "pontos_atividades": "6.00", "pontos_prova": "4.00",
        }, format="json")
        self.assertEqual(resposta.status_code, 200, resposta.json())

        self.api.force_login(self.aluno)
        dados = self.api.get(self.rota_aluno).json()
        self.assertEqual(dados["media_minima"], "5.01")
        self.assertEqual(dados["linhas"][0], {**linha_anterior, "situacao": "abaixo_da_media"})
        self.assertEqual(list(Nota.objects.order_by("pk").values_list("pk", "valor")), notas_anteriores)
