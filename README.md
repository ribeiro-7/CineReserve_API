# 🎬 CineReserve API

A API CineReserve é um backend RESTful escalável e de alto desempenho, projetado para gerenciar as complexidades das operações modernas de cinema. Construído com foco na integridade dos dados e no controle de concorrência, o sistema oferece um portal completo para que os cinéfilos descubram filmes, visualizem a disponibilidade de assentos em tempo real, reservem e comprem assentos disponíveis.

A documentação da API toda foi feita no POSTMAN, lá eu explico cada endpoint com exemplos na prática.
👇👇👇
## Link para documentação: https://documenter.getpostman.com/view/40491697/2sBXijJXRb

## 🚀 Como rodar o projeto com Docker

### 1. Clonar o repositório

```bash
git clone https://github.com/ribeiro-7/CineReserve_API
cd CineReserve_API
```

---

### 2. Criar arquivo `.env`

Crie um arquivo `.env` baseado no `.env.example`:

```env
DB_NAME=nome_do_seu_bd
DB_USER=user_do_db
DB_PASSWORD=senha_do_bd
DB_HOST=db
DB_PORT=5432

SECRET_KEY=CHANGE-ME
```

---

### 3. Subir os containers

```bash
docker-compose up --build
```

---

### 4. Rodar migrations

Em outro terminal:

```bash
docker-compose exec web python cinereserve_api/manage.py migrate
```

---

### 5. Criar superusuário (opcional)

```bash
docker-compose exec web python cinereserve_api/manage.py createsuperuser
```

---

### 6. Popular o banco (opcional)

```bash
docker-compose exec web python cinereserve_api/manage.py runscript populate
```

---

## 🌐 Acessos

* API: http://localhost:8000
* Admin: http://localhost:8000/admin

---

## 🛑 Parar o projeto

```bash
Ctrl + C
docker-compose down
```
