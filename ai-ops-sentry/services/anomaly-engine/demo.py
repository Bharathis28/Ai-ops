"""Demo script showing how to use trained anomaly detection models.

This script demonstrates:
1. Training a model
2. Loading a saved model
3. Making predictions on new data
4. Interpreting results
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using dynamic loading
import importlib.util

model_store_path = Path(__file__).parent / "infra" / "model_store.py"
model_store_spec = importlib.util.spec_from_file_location("model_store", model_store_path)
model_store_module = importlib.util.module_from_spec(model_store_spec)
model_store_spec.loader.exec_module(model_store_module)
ModelStore = model_store_module.ModelStore


def demo_load_and_predict():
    """Demo: Load a trained model and make predictions."""
    print("=" * 80)
    print("Demo: Loading Trained Model and Making Predictions")
    print("=" * 80)

    # Initialize model store
    store = ModelStore(base_path="./models", backend="local")

    # Check if model exists
    service_name = "frontend-api"
    if not store.model_exists(service_name):
        print(f"\n❌ No model found for '{service_name}'")
        print(f"   Please run: python services/anomaly-engine/main.py {service_name}")
        return

    print(f"\n✓ Loading model for service: {service_name}")
    model = store.load_model(service_name)
    metadata = store.load_metadata(service_name)

    print(f"\nModel Info:")
    print(f"  - Type: {metadata.get('model_type', 'Unknown')}")
    print(f"  - Samples trained on: {metadata.get('n_samples', 'Unknown')}")
    print(f"  - Features: {metadata.get('n_features', 'Unknown')}")
    print(f"  - Training anomaly rate: {metadata.get('training_anomaly_rate', 'Unknown')}%")
    print(f"  - Feature names: {metadata.get('feature_names', [])}")

    # Create test data: normal and anomalous
    print("\n" + "=" * 80)
    print("Test Data: Normal vs Anomalous Metrics")
    print("=" * 80)

    test_data = pd.DataFrame({
        "cpu_usage": [
            72.5,   # Normal
            68.0,   # Normal
            95.0,   # Anomaly - High CPU
            70.0,   # Normal
            100.0,  # Anomaly - Extreme CPU
        ],
        "memory_usage": [
            62.0,   # Normal
            58.0,   # Normal
            90.0,   # Anomaly - High Memory
            60.0,   # Normal
            55.0,   # Normal
        ],
        "latency_p95": [
            115.0,  # Normal
            125.0,  # Normal
            450.0,  # Anomaly - Very High Latency
            120.0,  # Normal
            110.0,  # Normal
        ],
        "request_rate": [
            1050.0,  # Normal
            980.0,   # Normal
            1100.0,  # Normal
            200.0,   # Anomaly - Very Low Traffic
            1020.0,  # Normal
        ],
        "error_rate": [
            0.5,    # Normal
            0.6,    # Normal
            15.0,   # Anomaly - High Error Rate
            0.4,    # Normal
            0.5,    # Normal
        ],
    })

    # Make predictions
    predictions = model.predict(test_data)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(test_data)  # Lower = more anomalous

    # Display results
    print("\nPredictions:")
    print("-" * 80)
    print(f"{'Index':<8} {'CPU':<8} {'Memory':<8} {'Latency':<10} {'Requests':<10} {'Errors':<8} {'Score':<12} {'Result':<10}")
    print("-" * 80)

    for i in range(len(test_data)):
        result = "🔴 ANOMALY" if predictions[i] == -1 else "✓ Normal"
        print(
            f"{i:<8} "
            f"{test_data.iloc[i]['cpu_usage']:<8.1f} "
            f"{test_data.iloc[i]['memory_usage']:<8.1f} "
            f"{test_data.iloc[i]['latency_p95']:<10.1f} "
            f"{test_data.iloc[i]['request_rate']:<10.1f} "
            f"{test_data.iloc[i]['error_rate']:<8.1f} "
            f"{scores[i]:<12.4f} "
            f"{result}"
        )

    print("-" * 80)

    # Summary
    n_anomalies = (predictions == -1).sum()
    anomaly_rate = (n_anomalies / len(test_data)) * 100

    print(f"\nSummary:")
    print(f"  - Total samples: {len(test_data)}")
    print(f"  - Detected anomalies: {n_anomalies}")
    print(f"  - Anomaly rate: {anomaly_rate:.1f}%")

    print("\n" + "=" * 80)
    print("Interpretation:")
    print("=" * 80)
    print("  - Anomaly Score: Lower scores indicate more anomalous behavior")
    print("  - Prediction = -1: Anomaly detected")
    print("  - Prediction = +1: Normal behavior")
    print("\nAnomalies are flagged when metrics deviate significantly from")
    print("the patterns learned during training.")
    print("=" * 80)


def demo_batch_scoring():
    """Demo: Score a batch of metrics from a DataFrame."""
    print("\n" + "=" * 80)
    print("Demo: Batch Scoring from DataFrame")
    print("=" * 80)

    store = ModelStore(base_path="./models", backend="local")
    service_name = "frontend-api"

    if not store.model_exists(service_name):
        print(f"❌ No model found for '{service_name}'")
        return

    model = store.load_model(service_name)

    # Create a larger batch of metrics
    np.random.seed(42)
    n_samples = 20

    batch = pd.DataFrame({
        "cpu_usage": np.random.normal(70, 10, n_samples),
        "memory_usage": np.random.normal(60, 8, n_samples),
        "latency_p95": np.random.normal(120, 15, n_samples),
        "request_rate": np.random.normal(1000, 100, n_samples),
        "error_rate": np.random.normal(0.5, 0.2, n_samples),
    })

    # Inject some anomalies
    batch.loc[5, "cpu_usage"] = 98.0
    batch.loc[10, "latency_p95"] = 400.0
    batch.loc[15, "error_rate"] = 12.0

    predictions = model.predict(batch)
    scores = model.decision_function(batch)

    # Show only anomalies
    anomaly_indices = np.where(predictions == -1)[0]

    print(f"\n✓ Scored {len(batch)} samples")
    print(f"  Found {len(anomaly_indices)} anomalies:\n")

    if len(anomaly_indices) > 0:
        print(f"{'Index':<8} {'CPU':<10} {'Memory':<10} {'Latency':<10} {'Errors':<10} {'Score'}")
        print("-" * 65)
        for idx in anomaly_indices:
            print(
                f"{idx:<8} "
                f"{batch.iloc[idx]['cpu_usage']:<10.2f} "
                f"{batch.iloc[idx]['memory_usage']:<10.2f} "
                f"{batch.iloc[idx]['latency_p95']:<10.2f} "
                f"{batch.iloc[idx]['error_rate']:<10.2f} "
                f"{scores[idx]:<10.4f}"
            )
    else:
        print("  No anomalies detected in this batch.")


if __name__ == "__main__":
    demo_load_and_predict()
    demo_batch_scoring()

    print("\n" + "=" * 80)
    print("✓ Demo completed!")
    print("=" * 80)
