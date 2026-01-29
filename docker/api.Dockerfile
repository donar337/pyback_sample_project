FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install poetry && \
    poetry lock && \
    poetry install --no-root

COPY app ./app
COPY shared ./shared
COPY alembic.ini ./

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
