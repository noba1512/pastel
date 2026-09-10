# Pastel da TATI

Sistema interno de PDV, caixa, estoque e gestão operacional para pastelaria.

Monólito Django server-rendered. O caixa registra vendas no balcão; gerente e administrador controlam produtos, estoque, vendas e usuários. Preço, total e estoque são recalculados no servidor. O navegador só acelera o gesto.

## Stack

- Python e Django
- Django Templates
- Tailwind CSS via CDN
- Vanilla JavaScript
- SQLite (padrão) ou PostgreSQL via variáveis de ambiente
- Docker e Docker Compose
- Autenticação nativa do Django, Groups e Permissions

## Requisitos

- Docker e Docker Compose, **ou**
- Python 3.12+ e as dependências de `requirements.txt`

## Como executar com Docker

```bash
cp .env.example .env
docker compose up --build
```

Abra http://localhost:8000

O container executa migrations, coleta static files e sobe o servidor. O arquivo SQLite fica em `./data` (volume no host).

Depois, quando necessário:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py setup_initial_data
docker compose exec web python manage.py create_demo_data
docker compose exec web python manage.py test
```

`create_demo_data` é opcional. Cria usuários e produtos **fictícios** (prefixo DEMO). Não é o cardápio real da Pastel da TATI.

Logins demo (somente se rodar o comando):

- `admin.demo` / `demo12345` — Administrador
- `gerente.demo` / `demo12345` — Gerente
- `caixa.demo` / `demo12345` — Caixa

## Como executar sem Docker

```bash
cp .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_initial_data
python manage.py createsuperuser
python manage.py runserver
```

Opcional:

```bash
python manage.py create_demo_data
```

## Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

No Docker:

```bash
docker compose exec web python manage.py migrate
```

## Superusuário

Não há senha administrativa no repositório.

```bash
python manage.py createsuperuser
```

ou

```bash
docker compose exec web python manage.py createsuperuser
```

O superusuário entra como administrador operacional.

## Setup inicial

```bash
python manage.py setup_initial_data
```

Idempotente. Cria os grupos:

- Administrador
- Gerente
- Caixa

e associa permissões de modelo.

## Testes

```bash
python manage.py test
```

ou

```bash
docker compose exec web python manage.py test
```

Cobre login, permissões, produto, estoque, finalização de venda, baixa, falta de estoque, total no backend, dinheiro/troco, cancelamento, devolução e exclusão de venda cancelada do faturamento.

## Variáveis de ambiente

| Variável | Padrão | Função |
|---|---|---|
| `SECRET_KEY` | chave de desenvolvimento | Chave Django |
| `DEBUG` | `1` | `1` liga debug |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:8000,...` | Origens CSRF |
| `DB_ENGINE` | `sqlite` | `sqlite` ou `postgres` |
| `SQLITE_PATH` | `data/db.sqlite3` | Caminho do SQLite |
| `DB_NAME` | `pastel` | Banco PostgreSQL |
| `DB_USER` | `pastel` | Usuário PostgreSQL |
| `DB_PASSWORD` | vazio | Senha PostgreSQL |
| `DB_HOST` | `localhost` | Host PostgreSQL |
| `DB_PORT` | `5432` | Porta PostgreSQL |

Veja `.env.example`.

## Trocar SQLite por PostgreSQL

1. Suba um PostgreSQL acessível.
2. No `.env`:

```env
DB_ENGINE=postgres
DB_NAME=pastel
DB_USER=pastel
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=5432
```

3. Rode `python manage.py migrate` (ou o equivalente no Docker).

O código já usa o backend `django.db.backends.postgresql` quando `DB_ENGINE=postgres`.

## Grupos

- **Caixa:** PDV, vendas próprias, sem cadastro de usuário, sem ajuste de estoque, sem dashboard.
- **Gerente:** dashboard, catálogo, estoque, vendas, cancelamento, consulta de usuários. Não é superuser.
- **Administrador:** tudo, inclusive criar e editar usuários.

## Fluxo do caixa

`/pdv/` — busca, categorias, grade de produtos, cupom à direita, pagamento, finalizar. Após a venda o pedido limpa e o número aparece na mesma tela.

Atalhos: `/` foca a busca, Enter adiciona o primeiro produto visível, F9 finaliza.
