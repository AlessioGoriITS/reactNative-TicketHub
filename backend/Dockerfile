FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts ./scripts
# The repository may be checked out on Windows, where shell scripts use CRLF.
# Normalise the entrypoint inside the Linux image before executing it.
RUN sed -i 's/\r$//' ./scripts/start.sh && chmod +x ./scripts/start.sh

EXPOSE 8000

CMD ["./scripts/start.sh"]
