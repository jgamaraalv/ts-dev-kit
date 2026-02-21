# Self-Hosting Next.js

Deploy Next.js outside of Vercel with confidence.

## Table of Contents

- [Standalone Output](#standalone-output)
- [ISR and Cache Handlers](#isr-and-cache-handlers)
- [What Works vs What Needs Setup](#what-works-vs-what-needs-setup)
- [Image Optimization](#image-optimization)
- [Environment Variables](#environment-variables)
- [OpenNext: Serverless Without Vercel](#opennext-serverless-without-vercel)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Testing Cache Handler](#testing-cache-handler)

## Standalone Output

For Docker or any containerized deployment, use standalone output:

```js
// next.config.js
export default {
  output: "standalone",
};
```

This creates a minimal `standalone` folder with only production dependencies:

```
.next/
├── standalone/
│   ├── server.js          # Entry point
│   ├── node_modules/      # Only production deps
│   └── .next/             # Build output
└── static/                # Must be copied separately
```

**Key points for containers:**

- Set `HOSTNAME="0.0.0.0"` for containers
- Copy `public/` and `.next/static/` separately (not included in standalone)
- Run with `node server.js`

## ISR and Cache Handlers

### The Problem

ISR (Incremental Static Regeneration) uses filesystem caching by default. This **breaks with multiple instances**:

- Instance A regenerates page -> saves to its local disk
- Instance B serves stale page -> doesn't see Instance A's cache
- Load balancer sends users to random instances -> inconsistent content

### Solution: Custom Cache Handler

Next.js 14+ supports custom cache handlers for shared storage:

```js
// next.config.js
import { resolve } from "node:path";

export default {
  cacheHandler: resolve("./cache-handler.js"),
  cacheMaxMemorySize: 0, // Disable in-memory cache
};
```

#### Redis Cache Handler Example

```js
// cache-handler.js
import { Redis } from "ioredis";

const redis = new Redis(process.env.REDIS_URL);
const CACHE_PREFIX = "nextjs:";

export default class CacheHandler {
  constructor(options) {
    this.options = options;
  }

  async get(key) {
    const data = await redis.get(CACHE_PREFIX + key);
    if (!data) return null;

    const parsed = JSON.parse(data);
    return {
      value: parsed.value,
      lastModified: parsed.lastModified,
    };
  }

  async set(key, data, ctx) {
    const cacheData = {
      value: data,
      lastModified: Date.now(),
    };

    if (ctx?.revalidate) {
      await redis.setex(CACHE_PREFIX + key, ctx.revalidate, JSON.stringify(cacheData));
    } else {
      await redis.set(CACHE_PREFIX + key, JSON.stringify(cacheData));
    }
  }

  async revalidateTag(tags) {
    // Implement tag-based invalidation
    // This requires tracking which keys have which tags
  }
}
```

## What Works vs What Needs Setup

| Feature              | Single Instance | Multi-Instance      | Notes                       |
| -------------------- | --------------- | ------------------- | --------------------------- |
| SSR                  | Yes             | Yes                 | No special setup            |
| SSG                  | Yes             | Yes                 | Built at deploy time        |
| ISR                  | Yes             | Needs cache handler | Filesystem cache breaks     |
| Image Optimization   | Yes             | Yes                 | CPU-intensive, consider CDN |
| Middleware           | Yes             | Yes                 | Runs on Node.js             |
| Edge Runtime         | Limited         | Limited             | Some features Node-only     |
| `revalidatePath/Tag` | Yes             | Needs cache handler | Must share cache            |
| `next/font`          | Yes             | Yes                 | Fonts bundled at build      |
| Draft Mode           | Yes             | Yes                 | Cookie-based                |

## Image Optimization

Next.js Image Optimization works out of the box but is CPU-intensive. For scale, offload to an external loader (Cloudinary, Imgix, etc.):

```js
// next.config.js
export default {
  images: {
    loader: "custom",
    loaderFile: "./lib/image-loader.js",
  },
};
```

```js
// lib/image-loader.js
export default function cloudinaryLoader({ src, width, quality }) {
  const params = ["f_auto", "c_limit", `w_${width}`, `q_${quality || "auto"}`];
  return `https://res.cloudinary.com/demo/image/upload/${params.join(",")}${src}`;
}
```

For simple setups, tune the built-in optimizer with `minimumCacheTTL` and limited `deviceSizes`.

## Environment Variables

### Build-time vs Runtime

```js
// Available at build time only (baked into bundle)
NEXT_PUBLIC_API_URL=https://api.example.com

// Available at runtime (server-side only)
DATABASE_URL=postgresql://...
API_SECRET=...
```

### Runtime Configuration

For truly dynamic config, don't use `NEXT_PUBLIC_*`. Instead:

```tsx
// app/api/config/route.ts
export async function GET() {
  return Response.json({
    apiUrl: process.env.API_URL,
    features: process.env.FEATURES?.split(","),
  });
}
```

## OpenNext: Serverless Without Vercel

[OpenNext](https://open-next.js.org/) adapts Next.js for AWS Lambda, Cloudflare Workers, etc. Supports AWS Lambda + CloudFront, Cloudflare Workers, Netlify Functions, and Deno Deploy.

## Pre-Deployment Checklist

1. **Build locally first**: `npm run build` - catch errors before deploy
2. **Test standalone output**: `node .next/standalone/server.js`
3. **Set `output: 'standalone'`** for Docker
4. **Configure cache handler** for multi-instance ISR
5. **Set `HOSTNAME="0.0.0.0"`** for containers
6. **Copy `public/` and `.next/static/`** - not included in standalone
7. **Add health check endpoint**
8. **Test ISR revalidation** after deployment
9. **Monitor memory usage** - Node.js defaults may need tuning

## Testing Cache Handler

**Critical**: Test your cache handler on every Next.js upgrade:

```bash
# Start multiple instances
PORT=3001 node .next/standalone/server.js &
PORT=3002 node .next/standalone/server.js &

# Trigger ISR revalidation
curl http://localhost:3001/api/revalidate?path=/posts

# Verify both instances see the update
curl http://localhost:3001/posts
curl http://localhost:3002/posts
# Should return identical content
```
