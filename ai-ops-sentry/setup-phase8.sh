#!/bin/bash
# Phase 8 - GCP Integration Setup Script
# Run this in Google Cloud Shell

set -e

PROJECT_ID="ai-ops-sentry"
REGION="us-central1"
SA_NAME="ai-ops-sentry-sa"
DATASET="ai_ops_metrics"

echo "AI Ops Sentry - Phase 8 Setup"
echo "================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Step 1: Set project
echo " Setting GCP project..."
gcloud config set project $PROJECT_ID

# Step 2: Enable APIs
echo " Enabling required APIs..."
gcloud services enable \
  container.googleapis.com \
  run.googleapis.com \
  bigquery.googleapis.com \
  pubsub.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

echo " APIs enabled"

# Step 3: Create Service Account
echo "Creating service account..."
gcloud iam service-accounts create $SA_NAME \
  --display-name="AI Ops Sentry Service Account" \
  --description="Service account for AI Ops Sentry services" \
  || echo "Service account already exists"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permissions
echo "🔐 Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

echo " Permissions granted"

# Step 4: Create BigQuery Dataset
echo " Creating BigQuery dataset..."
bq mk --dataset --location=US ${PROJECT_ID}:${DATASET} || echo "Dataset already exists"

# Create tables
echo " Creating BigQuery tables..."
bq mk --table ${PROJECT_ID}:${DATASET}.metrics \
  timestamp:TIMESTAMP,service_name:STRING,metric_name:STRING,value:FLOAT64,labels:STRING,source:STRING \
  || echo "Metrics table already exists"

bq mk --table ${PROJECT_ID}:${DATASET}.anomalies \
  timestamp:TIMESTAMP,service_name:STRING,metric_name:STRING,anomaly_score:FLOAT64,expected_value:FLOAT64,actual_value:FLOAT64,severity:STRING,description:STRING \
  || echo "Anomalies table already exists"

bq mk --table ${PROJECT_ID}:${DATASET}.actions \
  action_id:STRING,timestamp:TIMESTAMP,service_name:STRING,action_type:STRING,target_type:STRING,reason:STRING,status:STRING,triggered_by:STRING,result:STRING \
  || echo "Actions table already exists"

echo " BigQuery tables created"

# Step 5: Create Pub/Sub Topics
echo " Creating Pub/Sub topics..."
gcloud pubsub topics create metrics-ingestion || echo "Topic already exists"
gcloud pubsub topics create anomaly-alerts || echo "Topic already exists"
gcloud pubsub topics create action-events || echo "Topic already exists"

# Create subscriptions
echo " Creating Pub/Sub subscriptions..."
gcloud pubsub subscriptions create metrics-ingestion-sub \
  --topic=metrics-ingestion || echo "Subscription already exists"

gcloud pubsub subscriptions create anomaly-alerts-sub \
  --topic=anomaly-alerts || echo "Subscription already exists"

gcloud pubsub subscriptions create action-events-sub \
  --topic=action-events || echo "Subscription already exists"

echo " Pub/Sub configured"

# Step 6: Summary
echo ""
echo " Phase 8 Setup Complete!"
echo "=========================="
echo ""
echo " APIs Enabled"
echo " Service Account Created: $SA_EMAIL"
echo " BigQuery Dataset: $DATASET"
echo " BigQuery Tables: metrics, anomalies, actions"
echo " Pub/Sub Topics: metrics-ingestion, anomaly-alerts, action-events"
echo ""
echo " Next Steps:"
echo "1. Download service account key (for local dev):"
echo "   gcloud iam service-accounts keys create ai-ops-sentry-key.json \\"
echo "     --iam-account=$SA_EMAIL"
echo ""
echo "2. Update .env files with ENABLE_GCP_CLIENTS=true"
echo ""
echo "3. Uncomment BigQuery code in services"
echo ""
echo "4. Deploy to Cloud Run:"
echo "   cd services/ingestion-api && gcloud run deploy ingestion-api --source ."
echo "   cd services/action-engine && gcloud run deploy action-engine --source ."
echo "   cd services/anomaly-engine && gcloud run deploy anomaly-engine --source ."
echo ""
echo " Full guide: PHASE8_SETUP.md"
echo ""
