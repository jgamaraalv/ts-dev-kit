# Multi-Stage Dockerfile for Yarn 4 Monorepo

## API Dockerfile (`apps/api/Dockerfile`)

```dockerfile
# ============================================
# Stage 1: Base with Yarn 4 Berry
# ============================================
FROM node:22-alpine AS base
ENV YARN_ENABLE_GLOBAL_CACHE=false
WORKDIR /app

# Install Yarn Berry
COPY .yarnrc.yml ./
COPY .yarn/ .yarn/
COPY package.json yarn.lock ./

# ============================================
# Stage 2: Install ALL dependencies (for building)
# ============================================
FROM base AS deps
# Copy all workspace package.json files
COPY apps/api/package.json apps/api/
COPY apps/web/package.json apps/web/
COPY packages/shared/package.json packages/shared/
COPY packages/config/package.json packages/config/
RUN yarn install --immutable

# ============================================
# Stage 3: Build shared packages first
# ============================================
FROM deps AS builder
COPY . .
# Build in dependency order
RUN yarn workspace @myapp/shared build
RUN yarn workspace @myapp/api build
# Or for web: RUN yarn workspace @myapp/web build

# ============================================
# Stage 4: Production runtime (API)
# ============================================
FROM node:22-alpine AS api-runner
WORKDIR /app

# Security: non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Copy only production dependencies and built output
COPY --from=builder /app/apps/api/dist ./apps/api/dist
COPY --from=builder /app/apps/api/package.json ./apps/api/
COPY --from=builder /app/packages/shared/dist ./packages/shared/dist
COPY --from=builder /app/packages/shared/package.json ./packages/shared/
COPY --from=builder /app/package.json ./
COPY --from=builder /app/yarn.lock ./
COPY --from=builder /app/.yarnrc.yml ./
COPY --from=builder /app/.yarn/ ./.yarn/

# Install production dependencies only
RUN yarn workspaces focus @myapp/api --production && yarn cache clean

USER app
EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

CMD ["node", "apps/api/dist/index.js"]
```

## Layer Caching Order

```dockerfile
# 1. System dependencies (rarely change)
RUN apk add --no-cache ...

# 2. Package manifests (change on dependency update)
COPY package.json yarn.lock ./

# 3. Install dependencies (cached unless manifests change)
RUN yarn install --immutable

# 4. Source code (changes most frequently)
COPY . .

# 5. Build
RUN yarn build
```

## .dockerignore

```
.git
node_modules
*.md
.env*
.vscode
.claude
**/__tests__
**/*.test.ts
**/*.spec.ts
coverage
.turbo
```

## Size Reduction Tips

- Use Alpine-based images (`node:22-alpine`)
- Multi-stage builds to exclude build tools from final image
- `yarn cache clean` after install
- Don't copy `.git`, `node_modules`, or test files
- Use `--production` flag for runtime dependencies only
