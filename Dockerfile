# syntax=docker/dockerfile:1

FROM python:3.14-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


FROM python:3.14-slim-bookworm AS runtime

ARG BUILD_TAG=local

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000 \
    APP_NAME=PopShop \
    APP_VERSION=1.1.0 \
    BUILD_TAG=${BUILD_TAG}

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app wsgi.py ./
COPY --chown=app:app app/ ./app/

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health')"

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 2 --timeout 30 --access-logfile - --error-logfile - wsgi:app"]
