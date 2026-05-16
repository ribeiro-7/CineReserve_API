# 🎬 CineReserve API

A API CineReserve é um backend RESTful escalável e de alto desempenho, projetado para gerenciar as complexidades das operações modernas de cinema. Construído com foco na integridade dos dados e no controle de concorrência, o sistema oferece um portal completo para que os cinéfilos descubram filmes, visualizem a disponibilidade de assentos em tempo real, reservem e comprem assentos disponíveis.

# 📚 Documentação da API

A documentação da API foi desenvolvida utilizando:

- **Postman** → com exemplos práticos de uso dos endpoints, autenticação e fluxos da aplicação.
- **Swagger/OpenAPI** → gerada automaticamente com a biblioteca `drf-spectacular`, permitindo explorar e testar os endpoints diretamente pela interface web.
- **ReDoc** → interface alternativa baseada em OpenAPI, com documentação mais detalhada e organizada para leitura.

👇👇👇

## 🔗 Documentação no Postman
https://documenter.getpostman.com/view/40491697/2sBXqRibqf

---

## 🔗 Swagger UI (local)

Após rodar o projeto localmente:

```bash
http://localhost:8000/api/schema/swagger-ui/
```

O schema OpenAPI também pode ser acessado em:

```bash
http://localhost:8000/api/schema/
```

## 🔗 ReDoc (local)

```bash
http://localhost:8000/api/schema/redoc/
```

O ReDoc fornece:
- documentação mais organizada e detalhada
- navegação amigável entre endpoints
- visualização completa do schema OpenAPI

---

## 🔗 Schema OpenAPI

```bash
http://localhost:8000/api/schema/
```

## 🚀 Como rodar o projeto com Docker

### 1. Clonar o repositório

```bash
git clone https://github.com/ribeiro-7/CineReserve_API
cd CineReserve_API
```

---

### 2. Criar arquivo `.env`

Crie um arquivo `.env` baseado no `.env.example`:
O arquivo tem que ser criado na raiz do projeto.

Adicione as informações do seu banco de dados 👇

```env
# Database Settings
DB_NAME=nome_do_seu_bd
DB_USER=user_do_db
DB_PASSWORD=senha_do_bd
DB_HOST=db
DB_PORT=5432

# Django SECRET KEY
SECRET_KEY=CHANGE-ME

#Url do Broker do Celery
CELERY_BROKER_URL=url_do_broker

#Flutterwave 
FLW_PUBLIC_KEY = CHANGE-ME
FLW_SECRET_KEY = CHANGE-ME
FLW_ENCRYPTION_KEY = CHANGE-ME
FLW_SECRET_HASH = CHANGE-ME
FLW_REDIRECT_URL= CHANGE-ME
```

---

### 3. Subir os containers

```bash
docker-compose up
```

---

### 4. Rodar migrations

Em outro terminal:

```bash
docker-compose exec web python cinereserve_api/manage.py makemigrations
docker-compose exec web python cinereserve_api/manage.py migrate
```

---

### 5. Criar superusuário (opcional)

```bash
docker-compose exec web python cinereserve_api/manage.py createsuperuser
```

---

### 6. Popular o banco (opcional)

Fiz um Script chamado "Populate" para criar objetos no banco de dados mais facilmente com filmes, sessões, preços e cadeiras das sessões.

```bash
docker-compose exec web python cinereserve_api/manage.py runscript populate
```

---

## 🔐 Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/v1/auth/register/` | Registrar usuário |
| POST | `/api/v1/auth/login/` | Login JWT |
| POST | `/api/v1/auth/logout/` | Logout / Blacklist token |
| POST | `/api/v1/auth/refresh/` | Renovar access token |
| POST | `/api/v1/auth/verify/` | Verificar token |

---

## 🎬 Movies

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/movies/` | Listar filmes |
| GET | `/api/v1/movies/{id}/` | Detalhes do filme |
| POST | `/api/v1/movies/` | Criar filme (Admin) |
| PUT | `/api/v1/movies/{id}/` | Atualizar filme (Admin) |
| PATCH | `/api/v1/movies/{id}/` | Atualização parcial (Admin) |
| DELETE | `/api/v1/movies/{id}/` | Remover filme (Admin) |

---

## 🎟️ Sessions

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/sessions/` | Listar sessões |
| GET | `/api/v1/sessions/{id}/` | Detalhes da sessão |
| GET | `/api/v1/sessions/{id}/seats/` | Listar assentos da sessão |
| POST | `/api/v1/sessions/` | Criar sessão (Admin) |
| PUT | `/api/v1/sessions/{id}/` | Atualizar sessão (Admin) |
| PATCH | `/api/v1/sessions/{id}/` | Atualização parcial (Admin) |
| DELETE | `/api/v1/sessions/{id}/` | Remover sessão (Admin) |

---

## 🪑 Reservas e Compras

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/v1/sessions/{id}/reserve/` | Reservar assentos |
| POST | `/api/v1/sessions/{id}/buy/` | Comprar ingressos |

---

## 🎫 Tickets

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/tickets/` | Listar ingressos do usuário |
| GET | `/api/v1/tickets/{id}/` | Detalhes de um ingresso |

---

## 📦 Bookings

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/bookings/` | Listar reservas/compras do usuário |
| GET | `/api/v1/bookings/{id}/` | Detalhes de uma reserva/compra |

---

## 🛑 Parar o projeto

```bash
Ctrl + C
docker-compose down
```
