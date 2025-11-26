# AI-Ops Sentry Architecture

## Overview

This document describes the architecture of the AI-Ops Sentry system.

## Components

### Services

#### Metrics Collector
Collects metrics from various sources.

#### Ingestion API
API for ingesting metrics and events.

#### Anomaly Engine
- **Offline Trainer**: Trains anomaly detection models
- **Online Scorer**: Real-time anomaly scoring

#### Action Engine
Executes remediation actions based on detected anomalies.

#### Dashboard
Web-based visualization and monitoring interface.

## Infrastructure

- Terraform configurations for cloud resources
- Kubernetes manifests for container orchestration

## Libraries

- **Core**: Shared core utilities
- **Monitoring**: Monitoring and observability tools
- **Models**: Shared ML models and schemas
