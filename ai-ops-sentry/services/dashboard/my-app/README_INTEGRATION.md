# AI Ops Sentry Dashboard - Backend Integration

This Next.js dashboard is integrated with the AI Ops Sentry backend services (Phases 1-6).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Dashboard (Port 3000)               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  IntegratedDashboard Component                            │ │
│  │  - Fetches real data from backend APIs                    │ │
│  │  - Polls for updates every 5-30 seconds                   │ │
│  │  - Handles action triggers (restart, scale, rollout)      │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP REST APIs
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Ingestion API │    │ Action Engine │    │ Anomaly Data  │
│  (Port 8000)  │    │  (Port 8003)  │    │  (BigQuery)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

## Features

### ✅ Real-Time Data Integration
- **Services Health**: Polls backend every 15 seconds for service metrics
- **Anomalies**: Checks for new anomalies every 10 seconds
- **Backend Health**: Monitors Ingestion API and Action Engine connectivity

### ✅ Action Engine Integration
- **Restart Deployment**: Triggers GKE/Cloud Run service restarts
- **Scale Deployment**: Adjusts replica counts
- **Rollout Restart**: Zero-downtime rolling restarts (GKE only)

### ✅ Mock Data Fallback
- When Phase 8 (GCP integration) is not complete, uses realistic mock data
- Seamless transition to real BigQuery data when available
- Visual indicator when backend services are offline

## Configuration

### Environment Variables

Create `.env.local` with:

```bash
# Backend API URLs
NEXT_PUBLIC_INGESTION_API_URL=http://localhost:8000
NEXT_PUBLIC_ACTION_ENGINE_URL=http://localhost:8003
NEXT_PUBLIC_ANOMALY_ENGINE_URL=http://localhost:8001
```

### Production Configuration

For production deployment:

```bash
NEXT_PUBLIC_INGESTION_API_URL=https://ingestion-api-xxx.run.app
NEXT_PUBLIC_ACTION_ENGINE_URL=https://action-engine-xxx.run.app
NEXT_PUBLIC_ANOMALY_ENGINE_URL=https://anomaly-engine-xxx.run.app
```

## API Client

The dashboard uses a centralized API client (`lib/api-client.ts`) that:

1. **Handles all backend communication**
2. **Implements timeout and error handling**
3. **Provides mock data fallback**
4. **Type-safe with TypeScript interfaces**

### Usage Example

```typescript
import { apiClient } from '@/lib/api-client'

// Restart a service
const response = await apiClient.restartDeployment({
  service_name: 'payment-api',
  target_type: 'gke',
  cluster_name: 'prod-cluster',
  namespace: 'default',
  reason: 'High CPU usage detected',
})

// Scale a service
await apiClient.scaleDeployment({
  service_name: 'user-auth',
  target_type: 'cloud_run',
  region: 'us-central1',
  min_replicas: 5,
  max_replicas: 50,
  reason: 'Traffic surge',
})
```

## Running the Dashboard

### Development

```bash
# Install dependencies
cd services/dashboard/my-app
npm install

# Start development server
npm run dev
```

The dashboard will be available at http://localhost:3000

### Production Build

```bash
npm run build
npm start
```

## Backend Services Required

Before running the dashboard, ensure these services are running:

### 1. Ingestion API (Port 8000)
```bash
cd services/ingestion-api
python main.py
```

### 2. Action Engine (Port 8003)
```bash
cd services/action-engine
python main.py
```

### Verify Services
```bash
# Check Ingestion API
curl http://localhost:8000/health

# Check Action Engine
curl http://localhost:8003/api/v1/health
```

## Data Flow

### 1. Service Health Data
```
Dashboard → GET /api/v1/services (future endpoint)
         ↓
    Currently uses mock data
         ↓
    Phase 8: BigQuery aggregation
```

### 2. Anomaly Data
```
Dashboard → GET /api/v1/anomalies (future endpoint)
         ↓
    Currently uses mock data
         ↓
    Phase 8: BigQuery anomalies table
```

### 3. Action Execution
```
Dashboard → POST /api/v1/restart_deployment
         ↓
    Action Engine (WORKING NOW!)
         ↓
    KubernetesClient/CloudRunClient (stubbed)
         ↓
    Phase 8: Real GCP APIs
```

## Phase 7 vs Phase 8

### Phase 7 (Current) ✅
- Dashboard UI fully functional
- Mock data for services and anomalies
- Real Action Engine integration
- Health monitoring
- Polling and auto-refresh

### Phase 8 (Future)
When you complete Phase 8 (GCP Integration):

1. **Create BigQuery Endpoints**
   ```python
   # In ingestion-api/api/routes.py
   @router.get("/api/v1/services")
   async def get_services():
       # Query BigQuery metrics_raw
       # Aggregate by service_name
       # Calculate health status
       return services
   
   @router.get("/api/v1/anomalies")
   async def get_anomalies(limit: int = 50):
       # Query BigQuery anomalies table
       # Return recent anomalies
       return anomalies
   ```

2. **Update API Client**
   ```typescript
   // lib/api-client.ts
   // Remove getMockX() calls
   // Use real HTTP endpoints instead
   ```

3. **Uncomment GCP Integration**
   - Action Engine: Enable real K8s and Cloud Run clients
   - Ingestion API: Enable BigQuery writes
   - Online Scorer: Enable Pub/Sub

## Testing the Integration

### 1. Test Health Checks
```bash
# Dashboard should show green status for running services
# Open http://localhost:3000
```

### 2. Test Action Execution
```typescript
// In dashboard, click "Restart" on a service
// Should see:
// 1. Loading spinner
// 2. Success notification
// 3. New action in action log
// 4. Check backend logs for [STUB] messages
```

### 3. Test Mock Data
```typescript
// Services should show:
// - payment-api (critical)
// - user-auth (degraded)
// - inventory-svc (healthy)
// - notification-svc (healthy)

// Anomalies should show:
// - Recent anomaly detections
// - Severity levels
// - Metric values
```

## Troubleshooting

### Backend Connection Failed
```
⚠️ Backend Connection Issues: Ingestion API offline. Action Engine offline. Using mock data.
```
**Solution:** Start the backend services (see above)

### CORS Errors
If you see CORS errors in browser console:

1. **Check Action Engine CORS config** (already configured):
```python
# services/action-engine/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **For production**, update to specific origins:
```python
allow_origins=["https://dashboard.yourcompany.com"]
```

### Port Conflicts
If ports are already in use:

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :8003

# Kill process
taskkill /PID <PID> /F

# Or change ports in .env.local
```

## Next Steps

1. ✅ **Dashboard UI**: Complete (v0.dev design integrated)
2. ✅ **API Client**: Complete (with mock data fallback)
3. ✅ **Action Engine Integration**: Complete (restart, scale, rollout)
4. 🔄 **Phase 8 - BigQuery Integration**:
   - Create `/api/v1/services` endpoint in Ingestion API
   - Create `/api/v1/anomalies` endpoint
   - Query BigQuery for real data
   - Update API client to use real endpoints
5. 🔄 **Phase 8 - Full GCP**:
   - Deploy all services to Cloud Run
   - Enable real Kubernetes and Cloud Run operations
   - Set up IAM and service accounts
   - Configure production monitoring

## API Reference

### GET /api/v1/services (Future)
Returns aggregated service health data.

### GET /api/v1/anomalies (Future)
Returns recent anomaly detections.

### POST /api/v1/restart_deployment (Working Now!)
Restarts a GKE deployment or Cloud Run service.

### POST /api/v1/scale_deployment (Working Now!)
Scales a deployment to specified replica count.

### POST /api/v1/rollout_restart (Working Now!)
Performs zero-downtime rolling restart (GKE only).

---

**Status**: Phase 7 Complete ✅  
**Next**: Phase 8 - GCP Integration 🚀
