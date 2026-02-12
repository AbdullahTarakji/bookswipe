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
RUN flutter build web --dart-define=API_BASE_URL=http://localhost:8000

# Stage 2: Serve with nginx
FROM nginx:1.27.3-alpine

# Security: Add metadata labels
LABEL maintainer="BookSwipe Team"
LABEL description="BookSwipe Frontend"

# Security: Remove default nginx config and add custom one
RUN rm -rf /usr/share/nginx/html/*

# Security: Create nginx cache and pid directories writable by non-root
RUN mkdir -p /var/cache/nginx /var/run && \
    chown -R nginx:nginx /var/cache/nginx /var/run /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx /var/run

# Copy built web app from build stage
COPY --from=build --chown=nginx:nginx /app/build/web /usr/share/nginx/html

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
