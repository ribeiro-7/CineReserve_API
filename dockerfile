# imagem base
FROM python:3.12-slim

# variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# diretório dentro do container
WORKDIR /app

# copiar arquivos
COPY pyproject.toml poetry.lock /app/

# instalar poetry
RUN pip install poetry

# configurar poetry (sem criar venv dentro do container)
RUN poetry config virtualenvs.create false

# instalar dependências
RUN poetry install --no-interaction --no-ansi --no-root

# copiar o resto do projeto
COPY . /app/

# porta
EXPOSE 8000

# comando padrão
CMD ["python", "cinereserve_api/manage.py", "runserver", "0.0.0.0:8000"]