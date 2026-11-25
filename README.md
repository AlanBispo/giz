# Giz

O Giz usa React, Django e PostgreSQL. O acesso é por e-mail e senha, com uma tela inicial para cada perfil.

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
