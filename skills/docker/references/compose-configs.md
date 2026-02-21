# Docker Compose Configurations

## Development (`docker-compose.yml`)

Infrastructure services only — app runs natively via `yarn dev`.

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-myapp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-myapp}
      POSTGRES_DB: ${POSTGRES_DB:-myapp}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-myapp}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
  redis_data:
```

## Production Override (`docker-compose.prod.yml`)

Adds containerized app services on top of infrastructure.

```yaml
services:
  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
      target: api-runner
    restart: unless-stopped
    ports:
      - "3001:3001"
    environment:
      NODE_ENV: production
      DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
      target: web-runner
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      API_URL: http://api:3001
    depends_on:
      - api
```

## Health Checks

Every service should have a health check:

```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "--quiet", "http://localhost:3001/health"]
  interval: 30s
  timeout: 5s
  start_period: 10s
  retries: 3
```
