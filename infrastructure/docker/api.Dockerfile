# Expense Tracker API — multi-stage build.
# Hardened: build-arg base image (pin a digest in CI), non-root, minimal layers.

ARG PYTHON_IMAGE=python:3.12-slim

# ---------- builder ----------
FROM ${PYTHON_IMAGE} AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY services/api/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- runtime ----------
FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:${PATH}"

# Non-root runtime user
RUN groupadd --system app && useradd --system --gid app app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY services/api/app ./app
# Alembic migrations + config so the same immutable image can run
# `cd /app/database && alembic upgrade head` (used by the K8s initContainer).
COPY database ./database

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
