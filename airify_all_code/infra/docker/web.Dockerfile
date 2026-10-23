# Airify web (React/Vite) — multi-stage build → Nginx static serve.
# Build context is airify_all_code/ (see docker-compose.yml); the web app lives at apps/web.
# No secrets. VITE_* build args are optional; empty => "Coming soon / Join beta" in UI.

# ---- build stage ----
FROM node:20-alpine AS build
WORKDIR /app

# Optional public build-time config (safe placeholders; no secrets).
ARG VITE_API_BASE_URL=""
ARG VITE_PUBLIC_BASE_URL=""
ARG VITE_HEALTH_APP_URL=""
ARG VITE_APP_STORE_URL=""
ARG VITE_PLAY_STORE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_PUBLIC_BASE_URL=$VITE_PUBLIC_BASE_URL \
    VITE_HEALTH_APP_URL=$VITE_HEALTH_APP_URL \
    VITE_APP_STORE_URL=$VITE_APP_STORE_URL \
    VITE_PLAY_STORE_URL=$VITE_PLAY_STORE_URL

COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# ---- serve stage ----
FROM nginx:1.27-alpine
COPY infra/nginx/airify.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
