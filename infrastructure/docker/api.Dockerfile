# Expense Tracker API — multi-stage build.
# Phase 1 version; Phase 8 adds hardening (distroless/digest pinning, trivy gates).

# ---------- builder ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY services/api/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:${PATH}"

# Non-root runtime user
RUN groupadd --system app && useradd --system --gid app app

COPY --from=builder /install /usr/local

WORKDIR /app
COPY services/api/app ./app

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
