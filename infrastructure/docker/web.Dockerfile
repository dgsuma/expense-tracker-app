# Expense Tracker web (Flutter Web) — multi-stage build.
# Builds the Flutter web bundle, then serves it with nginx.

# ---------- builder ----------
FROM ghcr.io/cirruslabs/flutter:3.35.4 AS builder

WORKDIR /app

# Resolve dependencies first for better layer caching.
COPY apps/mobile/pubspec.yaml apps/mobile/pubspec.lock ./
RUN flutter pub get

# Build the web bundle. API_BASE_URL defaults to empty = same-origin /api calls
# (proxied by nginx), so the build is independent of host/IP.
COPY apps/mobile ./
ARG API_BASE_URL=
RUN flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}

# ---------- runtime ----------
FROM nginx:1.27-alpine AS runtime

# SPA + security-header config (listens on 8080).
COPY infrastructure/docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build/web /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD curl -f http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
