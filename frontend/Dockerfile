# Stage 1: Build Flutter web app
FROM debian:bookworm-20241223-slim AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git unzip xz-utils zip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch stable https://github.com/flutter/flutter.git /flutter
ENV PATH="/flutter/bin:${PATH}"

RUN flutter config --enable-web && flutter doctor

WORKDIR /app
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get

COPY . .

ARG API_BASE_URL=http://localhost:8000
RUN flutter build web --dart-define=API_BASE_URL=${API_BASE_URL}

# Stage 2: Serve with nginx
FROM nginx:1.27.3-alpine

LABEL maintainer="BookSwipe Team"
LABEL description="BookSwipe Frontend"

# Remove default nginx config and add custom SPA config
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Create nginx cache and pid directories writable by non-root
RUN mkdir -p /var/cache/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/run /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx /var/run

# Copy built web app from build stage
COPY --from=build --chown=nginx:nginx /app/build/web /usr/share/nginx/html

# SPA fallback — serve index.html for all non-file routes
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {\n\
        expires 30d;\n\
        add_header Cache-Control "public, immutable";\n\
        access_log off;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
