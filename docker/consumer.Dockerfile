FROM python:3.11-slim

WORKDIR /consumer

COPY pyproject.toml ./
RUN pip install poetry && \
    poetry lock && \
    poetry install --no-root

COPY consumer ./consumer
COPY shared ./shared

CMD ["poetry", "run", "python", "-m", "consumer.main"]
