# AI-Ops Sentry

An AI-powered operations monitoring and anomaly detection platform that helps identify and respond to issues in real-time.

## Overview

AI-Ops Sentry is a comprehensive platform for monitoring system metrics, detecting anomalies using machine learning, and automatically triggering remediation actions.

## Architecture

The system consists of several microservices:

- **Metrics Collector**: Gathers metrics from various sources
- **Ingestion API**: REST API for metric ingestion
- **Anomaly Engine**: ML-based anomaly detection
  - Offline Trainer: Trains detection models
  - Online Scorer: Real-time scoring
- **Action Engine**: Executes automated remediation
- **Dashboard**: Web-based monitoring interface

## Project Structure

```
ai-ops-sentry/
├── services/           # Microservices
│   ├── metrics-collector/
│   ├── ingestion-api/
│   ├── anomaly-engine/
│   │   ├── offline-trainer/
│   │   └── online-scorer/
│   ├── action-engine/
│   └── dashboard/
├── infra/             # Infrastructure as Code
│   ├── terraform/
│   └── k8s/
├── libs/              # Shared libraries
│   ├── core/
│   ├── monitoring/
│   └── models/
├── .github/           # CI/CD workflows
│   └── workflows/
└── docs/              # Documentation
    ├── architecture.md
    └── api-specs.md
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Kubernetes (optional, for production)
- Terraform (optional, for infrastructure)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-ops-sentry.git
cd ai-ops-sentry
```

2. Install dependencies:
```bash
pip install -r requirements.txt
# or using pyproject.toml
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Format code:
```bash
black .
ruff check .
```

### Running Services

Each service can be run independently:

```bash
# Example: Running the ingestion API
cd services/ingestion-api
python main.py
```

Or use Docker Compose for all services:
```bash
docker-compose up
```

## Deployment

### Kubernetes

Deploy to Kubernetes cluster:
```bash
kubectl apply -f infra/k8s/
```

### Terraform

Provision infrastructure:
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

## Documentation

- [Architecture Documentation](docs/architecture.md)
- [API Specifications](docs/api-specs.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Contact

For questions or support, please open an issue on GitHub.
