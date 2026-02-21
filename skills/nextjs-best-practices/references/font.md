# Font Optimization

Use `next/font` for automatic font optimization with zero layout shift.

## Table of Contents

- [Multiple Fonts with CSS Variables](#multiple-fonts-with-css-variables)
- [Local Fonts](#local-fonts)
- [Tailwind CSS v4 Integration](#tailwind-css-v4-integration)
- [Display Strategy](#display-strategy)
- [Common Mistakes](#common-mistakes)
- [Font in Specific Components](#font-in-specific-components)

## Multiple Fonts with CSS Variables

```tsx
import { Inter, Roboto_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-roboto-mono",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${robotoMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

Use in CSS:

```css
body {
  font-family: var(--font-inter);
}

code {
  font-family: var(--font-roboto-mono);
}
```

## Local Fonts

```tsx
import localFont from "next/font/local";

// Single file
const myFont = localFont({
  src: "./fonts/MyFont.woff2",
});

// Multiple files for different weights
const myFont = localFont({
  src: [
    {
      path: "./fonts/MyFont-Regular.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "./fonts/MyFont-Bold.woff2",
      weight: "700",
      style: "normal",
    },
  ],
});

// Variable font with CSS variable
const myFont = localFont({
  src: "./fonts/MyFont-Variable.woff2",
  variable: "--font-my-font",
});
```

## Tailwind CSS v4 Integration

In Tailwind v4, font families are configured via CSS variables (no `tailwind.config.js` needed):

```tsx
// app/layout.tsx
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
```

```css
/* globals.css — Tailwind v4 */
@import "tailwindcss";

@theme {
  --font-sans: var(--font-inter);
}
```

Then use `font-sans` utility class as normal.

## Display Strategy

Control font loading behavior:

```tsx
const inter = Inter({
  subsets: ["latin"],
  display: "swap", // Default - shows fallback, swaps when loaded
});

// Options:
// 'swap' - immediate fallback, swap when ready (recommended)
// 'block' - short block period, then swap
// 'fallback' - short block, short swap, then fallback
// 'optional' - short block, no swap (use if font is optional)
```

## Common Mistakes

```tsx
// Bad: Importing font in every component
// components/Button.tsx
import { Inter } from 'next/font/google'
const inter = Inter({ subsets: ['latin'] }) // Creates new instance each time!

// Good: Import once in layout, use CSS variable
// app/layout.tsx
const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

// Bad: Using @import in CSS (blocks rendering)
/* globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter');

// Good: Use next/font (self-hosted, no network request)
import { Inter } from 'next/font/google'

// Bad: Missing subset - loads all characters
const inter = Inter({})

// Good: Always specify subset
const inter = Inter({ subsets: ['latin'] })
```

## Font in Specific Components

```tsx
// For component-specific fonts, export from a shared file
// lib/fonts.ts
import { Inter, Playfair_Display } from "next/font/google";

export const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
export const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });

// components/Heading.tsx
import { playfair } from "@/lib/fonts";

export function Heading({ children }) {
  return <h1 className={playfair.className}>{children}</h1>;
}
```
