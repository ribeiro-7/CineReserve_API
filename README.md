# 🎬 CineReserve API

## 🚀 Como rodar o projeto com Docker

### 1. Clonar o repositório

```bash
git clone <seu-repo>
cd CineReserve_API
```

---

### 2. Criar arquivo `.env`

Crie um arquivo `.env` baseado no `.env.example`:

```env
DB_NAME=cinereserve_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=sua_chave_secreta
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
docker-compose down
```
