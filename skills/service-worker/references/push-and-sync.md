# Push Notifications & Background Sync

## Table of Contents

- [Push Notifications](#push-notifications)
  - [Subscribe from the Page](#subscribe-from-the-page)
  - [Send Push from Server](#send-push-from-server)
  - [Handle Push in SW](#handle-push-in-sw)
  - [Handle Notification Click](#handle-notification-click)
  - [VAPID Keys](#vapid-keys)
- [Background Sync](#background-sync)
  - [Register Sync from Page](#register-sync-from-page)
  - [Handle Sync in SW](#handle-sync-in-sw)
  - [Retry Pattern](#retry-pattern)
- [Periodic Background Sync](#periodic-background-sync)

## Push Notifications

### Subscribe from the Page

```js
async function subscribeToPush() {
  const reg = await navigator.serviceWorker.ready;

  // Check permission
  const permission = await Notification.requestPermission();
  if (permission !== "granted") return null;

  // Subscribe with VAPID public key
  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true, // Required: must show a notification for each push
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
  });

  // Send subscription to your server
  await fetch("/api/push/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(subscription),
  });

  return subscription;
}

// Helper: convert VAPID key
function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((char) => char.charCodeAt(0)));
}
```

### Send Push from Server

Using the `web-push` npm package (Node.js):

```js
import webpush from "web-push";

webpush.setVapidDetails(
  "mailto:admin@example.com",
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY,
);

// subscription = the PushSubscription JSON from the client
await webpush.sendNotification(
  subscription,
  JSON.stringify({
    title: "New message",
    body: "You have a new notification",
    icon: "/icon-192.png",
    url: "/messages",
  }),
);
```

Generate VAPID keys: `npx web-push generate-vapid-keys`

### Handle Push in SW

```js
self.addEventListener("push", (event) => {
  const data = event.data?.json() ?? {};
  const { title = "Notification", body, icon, url } = data;

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: icon || "/icon-192.png",
      badge: "/badge-72.png",
      data: { url }, // Pass URL to notificationclick handler
      vibrate: [100, 50, 100],
      actions: [
        { action: "open", title: "Open" },
        { action: "dismiss", title: "Dismiss" },
      ],
    }),
  );
});
```

### Handle Notification Click

```js
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "dismiss") return;

  const url = event.notification.data?.url || "/";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      // Focus existing tab if one matches
      for (const client of clients) {
        if (client.url === url && "focus" in client) {
          return client.focus();
        }
      }
      // Otherwise open a new window
      return self.clients.openWindow(url);
    }),
  );
});

self.addEventListener("notificationclose", (event) => {
  // Track dismissals (analytics)
});
```

### VAPID Keys

VAPID (Voluntary Application Server Identification) authenticates your server to the push service.

```bash
# Generate keys (do this once, store securely)
npx web-push generate-vapid-keys
```

Output:

```
Public Key:  BNbxG...  (use in client subscribe call)
Private Key: 3KW9e...  (use on server only, keep secret)
```

Store as environment variables:

```
VAPID_PUBLIC_KEY=BNbxG...
VAPID_PRIVATE_KEY=3KW9e...
```

## Background Sync

Defers actions until the user has connectivity. Chromium-only (Chrome, Edge).

> **Safari/iOS caveat:** Background Sync is not supported in Safari/iOS. Use periodic polling as fallback.

### Register Sync from Page

```js
async function saveForSync(data) {
  // Store the pending action in IndexedDB
  await saveToIndexedDB("pending-actions", data);

  // Register a sync
  const reg = await navigator.serviceWorker.ready;
  await reg.sync.register("sync-pending-actions");
}
```

### Handle Sync in SW

```js
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-pending-actions") {
    event.waitUntil(processPendingActions());
  }
});

async function processPendingActions() {
  const actions = await getFromIndexedDB("pending-actions");

  for (const action of actions) {
    try {
      await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(action),
      });
      await removeFromIndexedDB("pending-actions", action.id);
    } catch {
      // Will retry on next sync event
      throw new Error("Sync failed, will retry");
    }
  }
}
```

### Retry Pattern

The browser retries `sync` events with exponential backoff when the promise passed to `waitUntil` rejects. The event includes `event.lastChance` — if `true`, this is the final retry:

```js
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-form-data") {
    event.waitUntil(
      submitFormData().catch((err) => {
        if (event.lastChance) {
          // Final attempt failed — notify user via notification
          return self.registration.showNotification("Sync failed", {
            body: "Your data could not be submitted. Please try again.",
          });
        }
        throw err; // Reject to trigger retry
      }),
    );
  }
});
```

## Periodic Background Sync

Runs at periodic intervals even when the page is closed. Chromium-only, requires site engagement score.

```js
// Register from page
const reg = await navigator.serviceWorker.ready;
const status = await navigator.permissions.query({ name: "periodic-background-sync" });

if (status.state === "granted") {
  await reg.periodicSync.register("update-content", {
    minInterval: 24 * 60 * 60 * 1000, // Once per day minimum
  });
}

// Handle in SW
self.addEventListener("periodicsync", (event) => {
  if (event.tag === "update-content") {
    event.waitUntil(updateCachedContent());
  }
});

async function updateCachedContent() {
  const cache = await caches.open("content-v1");
  const response = await fetch("/api/latest-content");
  if (response.ok) {
    await cache.put("/api/latest-content", response);
  }
}
```

**Notes:**

- `minInterval` is a hint — the browser decides actual frequency based on site engagement
- Requires a minimum site engagement score (user must visit regularly)
- Not supported in Firefox or Safari
- Always check for API availability before registering
