from django.forms import modelform_factory
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from contas.models import Usuario
from contas.validators import LIMITE_SENHA

from .admin import EscolaAdmin, UsuarioCriacaoForm, site
from .models import Escola


class EstruturaEscolarTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.escola = Escola.objects.create(nome="Escola Giz")
        cls.usuarios = {
            perfil: Usuario.objects.create_user(username=perfil, perfil=perfil)
            for perfil in Usuario.Perfil
        }

    def setUp(self) -> None:
        self.api = APIClient()

    def _cadastrar(self, rota: str, dados: dict) -> dict:
        resposta = self.api.post(reverse(rota), dados, format="json")
        self.assertEqual(resposta.status_code, 201, resposta.data)
        return resposta.json()

    def test_coordenacao_cadastra_e_lista_estrutura_completa(self) -> None:
        self.api.force_login(self.usuarios[Usuario.Perfil.COORDENACAO])
        ano = self._cadastrar("ano-letivo-list", {"ano": 2027})
        bimestre = self._cadastrar("bimestre-list", {"ano_letivo": ano["id"], "numero": 1})
        turma = self._cadastrar("turma-list", {"ano_letivo": ano["id"], "nome": "7º A"})
        disciplina = self._cadastrar("disciplina-list", {"nome": "Matemática"})

        senha = "senha inicial de teste"
        professor = self._cadastrar("pessoa-list", {
            "nome": "Alex Souza", "email": "alex@example.com", "perfil": "professor", "senha": senha,
        })
        aluno = self._cadastrar("pessoa-list", {
            "nome": "Cris Silva", "email": "cris@example.com", "perfil": "aluno", "senha": senha,
        })
        self.assertNotIn("senha", professor)
        self.assertTrue(Usuario.objects.get(pk=professor["id"]).check_password(senha))
        vinculo = self._cadastrar("vinculo-list", {
            "professor": professor["id"], "turma": turma["id"], "disciplina": disciplina["id"],
        })
        matricula = self._cadastrar("matricula-list", {"aluno": aluno["id"], "turma": turma["id"]})
        aluno_admin = Usuario.objects.create_user(username="staff-aluno", is_staff=True)
        professor_admin = Usuario.objects.create_user(
            username="staff-professor", is_staff=True, perfil=Usuario.Perfil.PROFESSOR
        )

        for rota, registro in (
            ("ano-letivo-list", ano), ("bimestre-list", bimestre), ("turma-list", turma),
            ("disciplina-list", disciplina), ("pessoa-list", professor),
            ("vinculo-list", vinculo), ("matricula-list", matricula),
        ):
            with self.subTest(rota=rota):
                self.assertIn(registro, self.api.get(reverse(rota)).json())

        for rota, dados in (
            ("matricula-list", {"aluno": professor["id"], "turma": turma["id"]}),
            ("matricula-list", {"aluno": aluno["id"], "turma": turma["id"]}),
            ("matricula-list", {"aluno": aluno_admin.pk, "turma": turma["id"]}),
            ("vinculo-list", {
                "professor": aluno["id"], "turma": turma["id"], "disciplina": disciplina["id"],
            }),
            ("vinculo-list", {
                "professor": professor_admin.pk, "turma": turma["id"], "disciplina": disciplina["id"],
            }),
            ("bimestre-list", {"ano_letivo": ano["id"], "numero": 5}),
            ("pessoa-list", {
                "nome": "Outra pessoa", "email": "ALEX@example.com",
                "perfil": "aluno", "senha": senha,
            }),
            ("pessoa-list", {
                "nome": "Diretoria", "email": "dir@example.com", "perfil": "diretoria", "senha": senha,
            }),
        ):
            with self.subTest(rota=rota, dados=dados):
                self.assertEqual(self.api.post(reverse(rota), dados, format="json").status_code, 400)

    def test_so_coordenacao_e_diretoria_acessam_cadastros(self) -> None:
        rotas = (
            "pessoa-list", "ano-letivo-list", "bimestre-list", "turma-list",
            "disciplina-list", "vinculo-list", "matricula-list",
        )
        for usuario in (None, self.usuarios[Usuario.Perfil.ALUNO], self.usuarios[Usuario.Perfil.PROFESSOR]):
            self.api.logout()
            if usuario:
                self.api.force_login(usuario)
            for rota in rotas:
                with self.subTest(usuario=usuario, rota=rota):
                    url = reverse(rota)
                    self.assertEqual(self.api.get(url).status_code, 403)
                    self.assertEqual(self.api.post(url, {}, format="json").status_code, 403)

        self.api.force_login(self.usuarios[Usuario.Perfil.DIRETORIA])
        for rota in rotas:
            self.assertEqual(self.api.get(reverse(rota)).status_code, 200)
        self._cadastrar("disciplina-list", {"nome": "História"})

    def test_email_do_cadastro_funciona_no_login_apos_normalizar_o_dominio(self) -> None:
        self.api.force_login(self.usuarios[Usuario.Perfil.COORDENACAO])
        senha = "senha inicial de teste"
        email = "aluno@İstanbul.com"
        pessoa = self._cadastrar("pessoa-list", {
            "nome": "Aluno Unicode", "email": email, "perfil": "aluno", "senha": senha,
        })
        outro_email = "aluno@istanbul.com"
        outra_pessoa = self._cadastrar("pessoa-list", {
            "nome": "Outro aluno", "email": outro_email, "perfil": "aluno", "senha": senha,
        })

        longo = "a@" + ".".join(["İ" * 60] * 4) + ".com"
        resposta = self.api.post(reverse("pessoa-list"), {
            "nome": "E-mail longo", "email": longo, "perfil": "aluno", "senha": senha,
        }, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("O e-mail normalizado deve ter até 254 caracteres.", resposta.json()["email"])

        rotulo_longo = "a@" + "İ" * 32 + ".com"
        resposta = self.api.post(reverse("pessoa-list"), {
            "nome": "Domínio longo", "email": rotulo_longo, "perfil": "aluno", "senha": senha,
        }, format="json")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("email", resposta.json())

        for endereco, conta in ((email, pessoa), (outro_email, outra_pessoa)):
            with self.subTest(endereco=endereco):
                self.api.logout()
                resposta = self.api.post(
                    reverse("login"), {"email": endereco, "senha": senha}, format="json",
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.json()["id"], conta["id"])

    def test_senha_inicial_fraca_e_rejeitada(self) -> None:
        self.api.force_login(self.usuarios[Usuario.Perfil.COORDENACAO])
        for senha in ("a", " " * 12, "12345678"):
            with self.subTest(senha=senha):
                resposta = self.api.post(reverse("pessoa-list"), {
                    "nome": "Aluno", "email": "aluno@example.com", "perfil": "aluno", "senha": senha,
                }, format="json")
                self.assertEqual(resposta.status_code, 400)
                self.assertIn("senha", resposta.json())
        self.assertFalse(Usuario.objects.filter(email="aluno@example.com").exists())

    def test_regras_comecam_em_cinco_e_so_diretoria_altera(self) -> None:
        rota = reverse("regras-escola")
        self.api.force_login(self.usuarios[Usuario.Perfil.COORDENACAO])
        self.assertEqual(self.api.patch(rota, {"media_minima": "6.00"}, format="json").status_code, 403)

        self.api.force_login(self.usuarios[Usuario.Perfil.DIRETORIA])
        dados = self.api.get(rota).json()
        self.assertEqual(dados, {
            "nome": "Escola Giz", "media_minima": "5.00",
            "pontos_atividades": "5.00", "pontos_prova": "5.00",
        })
        resposta = self.api.patch(rota, {"media_minima": "6.50"}, format="json")
        self.assertEqual(resposta.status_code, 200)
        resposta = self.api.patch(rota, {"pontos_prova": "4.00"}, format="json")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["media_minima"], "6.50")
        self.assertEqual(
            self.api.patch(rota, {"pontos_prova": "-1.00"}, format="json").status_code, 400
        )

    def test_cadastro_e_edicao_exigem_csrf_da_sessao(self) -> None:
        self.api = APIClient(enforce_csrf_checks=True)
        self.api.force_login(self.usuarios[Usuario.Perfil.DIRETORIA])
        disciplina = reverse("disciplina-list")
        regras = reverse("regras-escola")
        self.assertEqual(self.api.post(disciplina, {"nome": "História"}, format="json").status_code, 403)
        self.assertEqual(self.api.patch(regras, {"media_minima": 6}, format="json").status_code, 403)
        token = self.api.get(reverse("csrf")).json()["csrfToken"]
        self.assertEqual(
            self.api.post(disciplina, {"nome": "História"}, format="json", HTTP_X_CSRFTOKEN=token).status_code,
            201,
        )
        self.assertEqual(
            self.api.patch(regras, {"media_minima": 6}, format="json", HTTP_X_CSRFTOKEN=token).status_code,
            200,
        )


class AdminEscolarTest(TestCase):
    def test_senha_inicial_da_diretoria_respeita_limite_do_login(self) -> None:
        senha = "🤖" * (LIMITE_SENHA + 1)
        form = UsuarioCriacaoForm(data={
            "username": "diretoria-limite",
            "email": "diretora@example.com",
            "perfil": Usuario.Perfil.DIRETORIA,
            "password1": senha,
            "password2": senha,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()["password2"][0].code, "max_length")

    def test_superusuario_cria_escola_e_primeira_diretoria(self) -> None:
        staff = Usuario.objects.create_user(username="staff", is_staff=True)
        self.client.force_login(staff)
        escola_add = reverse("admin:escolas_escola_add")
        self.assertEqual(self.client.get(escola_add).status_code, 302)

        root = Usuario.objects.create_superuser(username="root", password="senha de teste")
        self.client.force_login(root)
        resposta = self.client.post(escola_add, {"nome": "Escola Giz", "media_minima": "9.00"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Escola.objects.get().media_minima, 5)
        self.assertEqual(self.client.get(escola_add).status_code, 403)

        resposta = self.client.post(reverse("admin:contas_usuario_add"), {
            "username": "primeira-diretora",
            "first_name": "Diretora",
            "email": "diretora@example.com",
            "perfil": "diretoria",
            "password1": "senha inicial de teste",
            "password2": "senha inicial de teste",
        })
        self.assertEqual(resposta.status_code, 302)
        diretora = Usuario.objects.get(email="diretora@example.com")
        self.assertEqual(diretora.perfil, Usuario.Perfil.DIRETORIA)
        self.assertFalse(diretora.is_staff)
        self.assertTrue(diretora.check_password("senha inicial de teste"))

    def test_admin_altera_nome_sem_sobrescrever_uma_regra_concorrente(self) -> None:
        escola = Escola.objects.create(nome="Nome antigo")
        Escola.objects.filter(pk=escola.pk).update(media_minima=6)
        escola.nome = "Nome novo"
        form = modelform_factory(Escola, fields=("nome",))(instance=escola)

        EscolaAdmin(Escola, site).save_model(HttpRequest(), escola, form, change=True)

        escola.refresh_from_db()
        self.assertEqual(escola.nome, "Nome novo")
        self.assertEqual(escola.media_minima, 6)
