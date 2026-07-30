FROM node:20-alpine as base

LABEL maintainer="Covenexa Engineering"
LABEL description="Covenexa Frontend — React Web Application"

WORKDIR /app

# Install dependencies first (for layer caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source
COPY . .

# ── DEVELOPMENT TARGET ─────────────────────────────────────────
FROM base as development
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── PRODUCTION BUILD ───────────────────────────────────────────
FROM base as builder
RUN npm run build

# ── PRODUCTION RUNTIME (Nginx Server) ──────────────────────────
FROM nginx:alpine as production
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy default config to handle routing fallback to index.html
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
