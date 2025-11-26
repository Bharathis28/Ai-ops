"""Main entry point for the Anomaly Engine offline trainer.

This script trains IsolationForest models on historical metrics data
and saves them for use by the online anomaly detector.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using dynamic loading to handle hyphenated directory names
import importlib.util

# Load domain modules
features_path = Path(__file__).parent / "domain" / "features.py"
features_spec = importlib.util.spec_from_file_location("features", features_path)
features_module = importlib.util.module_from_spec(features_spec)
features_spec.loader.exec_module(features_module)
build_feature_matrix = features_module.build_feature_matrix

trainer_path = Path(__file__).parent / "domain" / "trainer.py"
trainer_spec = importlib.util.spec_from_file_location("trainer", trainer_path)
trainer_module = importlib.util.module_from_spec(trainer_spec)
trainer_spec.loader.exec_module(trainer_module)
train_isolation_forest = trainer_module.train_isolation_forest
get_model_metadata = trainer_module.get_model_metadata

# Load infra modules
bq_reader_path = Path(__file__).parent / "infra" / "bq_reader.py"
bq_reader_spec = importlib.util.spec_from_file_location("bq_reader", bq_reader_path)
bq_reader_module = importlib.util.module_from_spec(bq_reader_spec)
bq_reader_spec.loader.exec_module(bq_reader_module)
load_historical_metrics = bq_reader_module.load_historical_metrics

model_store_path = Path(__file__).parent / "infra" / "model_store.py"
model_store_spec = importlib.util.spec_from_file_location("model_store", model_store_path)
model_store_module = importlib.util.module_from_spec(model_store_spec)
model_store_spec.loader.exec_module(model_store_module)
ModelStore = model_store_module.ModelStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Train anomaly detection models for AI Ops Sentry",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "service_name",
        type=str,
        help="Name of the service to train a model for (e.g., 'frontend-api')",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of historical data to use for training",
    )

    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Expected proportion of outliers in the dataset (0.0 to 0.5)",
    )

    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in the IsolationForest",
    )

    parser.add_argument(
        "--model-dir",
        type=str,
        default="./models",
        help="Directory to save trained models",
    )

    parser.add_argument(
        "--fill-strategy",
        type=str,
        default="median",
        choices=["median", "mean", "zero", "drop"],
        help="Strategy for handling missing values in features",
    )

    parser.add_argument(
        "--csv-file",
        type=str,
        help="Optional: Load data from CSV file instead of BigQuery",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the offline trainer.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("=" * 80)
    logger.info("AI Ops Sentry - Anomaly Detection Model Trainer")
    logger.info("=" * 80)
    logger.info(f"Service: {args.service_name}")
    logger.info(f"Training data: {args.days} days")
    logger.info(f"Model directory: {args.model_dir}")
    logger.info("=" * 80)

    try:
        # Step 1: Load historical metrics
        logger.info("Step 1: Loading historical metrics...")
        if args.csv_file:
            logger.info(f"Loading from CSV: {args.csv_file}")
            load_metrics_from_csv = bq_reader_module.load_metrics_from_csv
            df_raw = load_metrics_from_csv(args.csv_file)
            # Filter by service name
            df_raw = df_raw[df_raw["service_name"] == args.service_name]
        else:
            df_raw = load_historical_metrics(
                service_name=args.service_name,
                days=args.days,
            )

        if df_raw.empty:
            logger.error(f"No data found for service: {args.service_name}")
            return 1

        logger.info(f"Loaded {len(df_raw)} data points")
        logger.info(f"Date range: {df_raw['timestamp'].min()} to {df_raw['timestamp'].max()}")

        # Step 2: Build feature matrix
        logger.info("Step 2: Building feature matrix...")
        X = build_feature_matrix(df_raw, fill_strategy=args.fill_strategy)

        if X.empty:
            logger.error("Feature matrix is empty after processing")
            return 1

        logger.info(f"Feature matrix shape: {X.shape}")
        logger.info(f"Features: {list(X.columns)}")

        # Log feature statistics
        logger.info("\nFeature statistics:")
        logger.info(f"\n{X.describe()}")

        # Step 3: Train model
        logger.info("Step 3: Training IsolationForest model...")
        model = train_isolation_forest(
            X,
            contamination=args.contamination,
            n_estimators=args.n_estimators,
        )

        logger.info("Model training completed successfully!")

        # Step 4: Extract metadata
        logger.info("Step 4: Extracting model metadata...")
        metadata = get_model_metadata(model, X)
        metadata["service_name"] = args.service_name
        metadata["training_days"] = args.days
        metadata["fill_strategy"] = args.fill_strategy

        logger.info(f"Model metadata: {metadata}")

        # Step 5: Save model
        logger.info("Step 5: Saving model...")
        store = ModelStore(base_path=args.model_dir, backend="local")
        model_path = store.save_model(
            service_name=args.service_name,
            model=model,
            metadata=metadata,
        )

        logger.info(f"Model saved successfully to: {model_path}")

        # Summary
        logger.info("=" * 80)
        logger.info("Training Summary:")
        logger.info(f"  Service: {args.service_name}")
        logger.info(f"  Samples: {metadata['n_samples']}")
        logger.info(f"  Features: {metadata['n_features']}")
        logger.info(f"  Training anomaly rate: {metadata['training_anomaly_rate']}%")
        logger.info(f"  Model saved to: {model_path}")
        logger.info("=" * 80)
        logger.info("✓ Training completed successfully!")

        return 0

    except Exception as e:
        logger.exception(f"Training failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
