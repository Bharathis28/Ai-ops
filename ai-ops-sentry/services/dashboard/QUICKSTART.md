# 🚀 AI Ops Sentry - Quick Start Guide

## Backend Integration Complete! ✅

Your v0.dev dashboard is now fully integrated with the AI Ops Sentry backend services.

## What's Working

### ✅ Dashboard Features
- **Real-time Service Monitoring** (mock data until Phase 8)
- **Anomaly Detection View** (mock data until Phase 8)
- **Action Execution** (REAL - connected to Action Engine!)
- **Backend Health Monitoring** (REAL - shows service status)
- **Auto-refresh** (polls every 5-30 seconds)

### ✅ Connected Backend Services
- **Ingestion API** (Port 8000) - Health check working
- **Action Engine** (Port 8003) - All actions working
  - Restart deployments ✅
  - Scale deployments ✅
  - Rollout restarts ✅

## Quick Start

### 1. Start Backend Services

```bash
# Terminal 1: Start Ingestion API
cd "c:\Users\Admin\New folder\Ai-ops\ai-ops-sentry\services\ingestion-api"
python main.py

# Terminal 2: Start Action Engine
cd "c:\Users\Admin\New folder\Ai-ops\ai-ops-sentry\services\action-engine"
python main.py
```

### 2. Start Dashboard

```bash
# Terminal 3: Start Dashboard
cd "c:\Users\Admin\New folder\Ai-ops\ai-ops-sentry\services\dashboard\my-app"
npm run dev
```

### 3. Open Dashboard

Open your browser to: **http://localhost:3002** (or port shown in terminal)

## Testing the Integration

### Test 1: Check Backend Health
1. Open dashboard
2. Look for green indicators showing backend connectivity
3. If services are offline, you'll see a warning banner

### Test 2: Trigger a Restart Action
1. Navigate to "Services" tab
2. Click on a service (e.g., "payment-api")
3. Click "Restart" button
4. Watch for:
   - Loading state
   - Success notification
   - New entry in "Recent Actions" list
5. Check Action Engine terminal - you should see:
   ```
   [STUB] Would delete pods for deployment payment-api in namespace default
   ```

### Test 3: Trigger a Scale Action
1. Click on a service
2. Click "Scale" button
3. Enter new replica count (e.g., 5)
4. Watch for success
5. Check Action Engine logs for:
   ```
   [STUB] Would scale deployment payment-api to 5 replicas
   ```

### Test 4: View Action History
1. Navigate to "Actions" tab
2. See list of all actions (manual and auto)
3. Each action shows:
   - Timestamp
   - Service name
   - Action type (restart/scale/rollout)
   - Result (success/failed/pending)
   - Triggered by (manual/auto)

## What You'll See

### Mock Data (Phase 7)
Until Phase 8 is complete, you'll see realistic mock data for:
- **Services**: payment-api, user-auth, inventory-svc, notification-svc
- **Anomalies**: Recent anomaly detections with scores
- **Metrics**: CPU, memory, latency, error rates

### Real Data (Action Engine)
These are connected to real backend now:
- **Action Execution**: Restart, scale, rollout requests
- **Action History**: Real action tracking with UUIDs
- **Health Checks**: Real HTTP health endpoints

## File Structure

```
services/dashboard/my-app/
├── lib/
│   ├── api-client.ts          # 🆕 Backend API integration
│   └── config.ts               # 🆕 API URLs and endpoints
├── components/
│   └── integrated-dashboard.tsx # 🆕 Connected dashboard wrapper
├── app/
│   └── page.tsx                # Updated to use integrated dashboard
├── dashboard.tsx               # Original v0.dev design
├── .env.local                  # 🆕 Backend service URLs
└── README_INTEGRATION.md       # 🆕 Integration docs
```

## Environment Configuration

The `.env.local` file configures backend URLs:

```bash
NEXT_PUBLIC_INGESTION_API_URL=http://localhost:8000
NEXT_PUBLIC_ACTION_ENGINE_URL=http://localhost:8003
NEXT_PUBLIC_ANOMALY_ENGINE_URL=http://localhost:8001
```

**For production**, update these to your Cloud Run URLs.

## API Client Features

The `api-client.ts` provides:

```typescript
// Health checks
await apiClient.checkIngestionAPIHealth()
await apiClient.checkActionEngineHealth()

// Get data (mock for now, real in Phase 8)
const services = await apiClient.getServices()
const anomalies = await apiClient.getAnomalies(50)
const metrics = await apiClient.getMetrics(['payment-api'])

// Execute actions (REAL - working now!)
await apiClient.restartDeployment({
  service_name: 'payment-api',
  target_type: 'gke',
  cluster_name: 'prod-cluster',
  namespace: 'default',
  reason: 'High CPU detected',
})

await apiClient.scaleDeployment({
  service_name: 'user-auth',
  target_type: 'cloud_run',
  region: 'us-central1',
  min_replicas: 5,
  max_replicas: 50,
  reason: 'Traffic surge',
})

await apiClient.rolloutRestart({
  service_name: 'inventory-svc',
  target_type: 'gke',
  cluster_name: 'prod-cluster',
  namespace: 'default',
  reason: 'Config update',
})
```

## Troubleshooting

### "Backend Connection Issues" Banner
**Cause**: Backend services not running  
**Fix**: Start Ingestion API and Action Engine (see Quick Start above)

### Port 3000 in use
**Cause**: Another process using port 3000  
**Fix**: Dashboard automatically uses port 3002 or next available port

### CORS Errors
**Cause**: CORS not enabled on backend  
**Fix**: Already configured in Action Engine `main.py`

### Actions Not Working
**Cause**: Action Engine not running  
**Fix**: Start Action Engine and refresh dashboard

## Next Steps

### Immediate (Phase 7 Complete ✅)
- ✅ Dashboard UI integrated
- ✅ Action Engine connected
- ✅ Health monitoring working
- ✅ Mock data displaying

### Phase 8 - GCP Integration
To get real metrics and anomalies:

1. **Add BigQuery Endpoints** to Ingestion API:
   ```python
   @router.get("/api/v1/services")
   @router.get("/api/v1/anomalies")
   ```

2. **Uncomment BigQuery Code**:
   - Ingestion API: `bq_writer.py`
   - Anomaly Engine: `anomaly_writer.py`

3. **Enable Real GCP Operations**:
   - Action Engine: `k8s_client.py`, `cloud_run_client.py`
   - Uncomment all `# TODO` sections

4. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ingestion-api --source .
   gcloud run deploy action-engine --source .
   ```

5. **Update Dashboard Config**:
   ```bash
   NEXT_PUBLIC_INGESTION_API_URL=https://ingestion-api-xxx.run.app
   NEXT_PUBLIC_ACTION_ENGINE_URL=https://action-engine-xxx.run.app
   ```

## Support

Check these files for detailed information:
- `README_INTEGRATION.md` - Full integration guide
- `lib/api-client.ts` - API client implementation
- `lib/config.ts` - Configuration options

## Demo Video Script

1. **Show Dashboard Home** - Overview with service health
2. **Navigate to Anomalies** - View detected anomalies
3. **Click on Service** - Show service details
4. **Trigger Restart** - Watch action execute
5. **Check Actions Tab** - See action history
6. **Show Backend Logs** - Prove integration working

---

**Status**: Phase 7 Dashboard ✅ COMPLETE  
**Backend**: Fully Integrated with Action Engine  
**Next**: Phase 8 - Full GCP Integration 🚀
