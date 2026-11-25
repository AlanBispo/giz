# Giz

O Giz usa React, Django e PostgreSQL. O acesso é por e-mail e senha. Coordenação e diretoria podem cadastrar a estrutura escolar, e a diretoria configura as regras de avaliação.

## Requisitos

- Windows com Python 3.12 e Node.js 24 LTS com npm.
- WSL com Docker e Docker Compose em execução.

## Executar localmente

No PowerShell, na raiz do projeto, copie o arquivo de configuração:

```powershell
Copy-Item .env.example .env
```

Preencha `DJANGO_SECRET_KEY` no `.env` com um valor aleatório próprio. Gere uma senha de 64 caracteres hexadecimais para `POSTGRES_PASSWORD`:

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
```

Copie a saída para `POSTGRES_PASSWORD` no `.env`. O formato hexadecimal evita que o Docker Compose e o Django interpretem caracteres especiais de formas diferentes. Suba o banco pelo Docker do WSL:

```powershell
wsl docker compose up -d --wait postgres
```

No mesmo terminal, prepare e inicie o backend no Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

Em outro terminal PowerShell, a partir da raiz do projeto, inicie o frontend:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Abra [o Giz](http://localhost:5173) para entrar com uma conta existente. Para preparar um usuário local, abra o shell do Django em `backend/`:

```powershell
..\.venv\Scripts\python.exe manage.py shell
```

```python
from getpass import getpass
from contas.models import Usuario

Usuario.objects.create_user(
    username="aluno-local",
    first_name="Aluno",
    email="aluno@example.com",
    password=getpass("Senha: "),
    perfil=Usuario.Perfil.ALUNO,
)
```

Contas antigas sem e-mail precisam de um endereço para entrar. Se a migração apontar e-mails duplicados, atribua endereços distintos às contas afetadas antes de rodar `migrate` novamente. O login não diferencia maiúsculas e minúsculas no e-mail.

Se a migração apontar um perfil inválido em uma conta existente, ajuste-o para aluno, professor, coordenação ou diretoria antes de rodar `migrate` novamente.

A página [Saúde do Giz](http://localhost:5173/saude) consulta `/api/saude/` pelo proxy do Vite, que encaminha as requisições ao Django na porta 8000. O Django consulta o PostgreSQL em `localhost:5432` e retorna `{"status": "ok"}` quando o banco está disponível ou HTTP 503 quando está indisponível.

## Preparar a gestão escolar

Em `backend/`, depois de aplicar as migrações, crie o superusuário do Django:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser
```

Abra o [admin do Django em 127.0.0.1](http://127.0.0.1:8000/admin/) e entre com o nome de usuário e a senha do superusuário. Use esse endereço para manter a sessão do admin separada da sessão do Giz em `localhost`.

1. Em **Escolas**, adicione a escola. A média mínima, os pontos de atividades e os pontos da prova começam em **5,0** cada.
2. Em **Usuários**, adicione a primeira conta com perfil **Diretoria**, e-mail e senha inicial. Para testar o acesso da coordenação, crie também uma conta com perfil **Coordenação**.
3. No [Giz](http://localhost:5173), entre com o e-mail de uma dessas contas e abra **Gestão escolar**. Cadastre anos letivos, bimestres, turmas, disciplinas, professores, alunos, vínculos docentes e matrículas. A diretoria também pode abrir **Regras de avaliação** e alterar os valores.

## Publicar e consultar atividades e provas

No perfil **Professor**, abra **Atividades e provas**, escolha uma turma, disciplina e bimestre e consulte o saldo antes de publicar. Cada período aceita uma prova por turma e disciplina. A prova recebe o valor configurado no momento da publicação e mantém esse valor ao mudar de período. O perfil **Aluno** usa a mesma tela para consultar as publicações das turmas em que está matriculado.

## Lançar e consultar notas

Em **Atividades e provas**, o professor abre **Lançar notas** na publicação e salva as notas dos alunos matriculados na turma. Zero é uma nota válida. Campos em branco de alunos ainda sem nota podem ficar para outro lançamento.

O aluno consulta **Minhas notas**, enquanto coordenação e diretoria consultam **Notas da escola**. Uma publicação com notas pode ter seu título, descrição e data corrigidos. O valor precisa continuar pelo menos igual à maior nota já lançada, e a publicação mantém turma, disciplina, bimestre e tipo.

## Consultar o boletim

O aluno abre **Meu boletim** para ver as próprias notas por disciplina e bimestre. Coordenação e diretoria abrem **Boletim por turma** e escolhem uma turma. O boletim soma as notas lançadas de atividades e da prova. Quando a diretoria altera a média mínima, o boletim recalcula a situação com a regra vigente e preserva as notas lançadas.

## Verificações

Em `backend/`, com o PostgreSQL em execução:

```powershell
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
```

Em `frontend/`, após `npm ci`:

```powershell
npm run lint
npm run build
```
