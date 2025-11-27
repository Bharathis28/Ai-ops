# Dashboard Setup Notes

## Issues Fixed

### 1. PostCSS Configuration Mismatch
**Problem**: The `postcss.config.mjs` was configured for Tailwind CSS v4 (`@tailwindcss/postcss`), but the project uses Tailwind CSS v3.4.17.

**Fix**: Updated `postcss.config.mjs` to use the standard Tailwind CSS v3 configuration:
```javascript
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

### 2. Tailwind Config HSL Color Syntax
**Problem**: Tailwind CSS requires `<alpha-value>` placeholder for HSL colors to support opacity modifiers.

**Fix**: Updated all HSL color definitions in `tailwind.config.js` to include the alpha-value placeholder:
```javascript
// Before
border: "hsl(var(--border))"

// After
border: "hsl(var(--border) / <alpha-value>)"
```

Applied to all color definitions:
- border, input, ring, background, foreground
- primary, secondary, destructive, muted, accent, popover, card (with their foreground variants)

### 3. Global CSS Apply Directives
**Problem**: The `@apply` directive was trying to use custom utility classes (`border-border`, `bg-background`, `text-foreground`) before Tailwind could generate them.

**Fix**: Replaced `@apply` with direct CSS in `app/globals.css`:
```css
/* Before */
@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* After */
@layer base {
  body {
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
  }
}
```

## Dashboard Access

The dashboard is now running at:
- **Local**: http://localhost:3000
- **Network**: http://10.10.3.51:3000

## API Integration

The dashboard connects to the following backend services:

1. **Ingestion API** (Port 8000)
   - Endpoint: `http://localhost:8000`
   - Purpose: Metrics collection and retrieval

2. **Action Engine** (Port 8003)
   - Endpoint: `http://localhost:8003`
   - Purpose: Auto-remediation actions (restart, scale, rollout)

API integration is implemented in `lib/api.ts` with automatic fallback to mock data when backends are unavailable.

## Environment Configuration

Environment variables are configured in `.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_INGESTION_API_URL=http://localhost:8000
NEXT_PUBLIC_ACTION_ENGINE_URL=http://localhost:8003
```

## Development

To start the dashboard:
```bash
cd services/dashboard/my-app
npm run dev
```

To build for production:
```bash
npm run build
npm start
```

## Dashboard Features

- **Overview**: System health, recent anomalies, active alerts
- **Anomalies**: List with severity, root cause analysis, filtering
- **Services**: Per-service metrics (CPU, memory, latency, errors)
- **Actions**: History of restarts, scaling, rollouts
- **Settings**: Environment selection, notifications, thresholds

## Tech Stack

- Next.js 15.5.6
- React 19.2.0
- Tailwind CSS 3.4.17
- shadcn/ui components
- Lucide React icons
- TypeScript 5
