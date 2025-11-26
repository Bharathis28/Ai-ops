"""Model training for anomaly detection.

This module provides functions to train IsolationForest models
on historical metrics data.
"""

import logging
from typing import Dict, Any

import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

# Default hyperparameters for IsolationForest
DEFAULT_CONTAMINATION = 0.05  # Expected proportion of anomalies (5%)
DEFAULT_N_ESTIMATORS = 100
DEFAULT_MAX_SAMPLES = "auto"
DEFAULT_RANDOM_STATE = 42  # Reproducibility


def train_isolation_forest(
    X: pd.DataFrame,
    contamination: float = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    max_samples: Any = DEFAULT_MAX_SAMPLES,
    random_state: int = DEFAULT_RANDOM_STATE,
    **kwargs,
) -> IsolationForest:
    """Train an IsolationForest model for anomaly detection.

    IsolationForest is an unsupervised algorithm that isolates anomalies by
    randomly selecting features and split values. Anomalies are easier to
    isolate and thus have shorter path lengths in the trees.

    Public interface is stable - hyperparameters can be adjusted without
    changing the function signature (use **kwargs for additional params).

    Args:
        X: Feature matrix (n_samples × n_features).
        contamination: Expected proportion of outliers in the dataset.
            Should be in (0, 0.5]. Default is 0.05 (5%).
        n_estimators: Number of trees in the forest. More trees = more stable
            predictions but slower training. Default is 100.
        max_samples: Number of samples to draw for training each tree.
            "auto" uses min(256, n_samples). Default is "auto".
        random_state: Random seed for reproducibility. Default is 42.
        **kwargs: Additional parameters to pass to IsolationForest.

    Returns:
        Trained IsolationForest model.

    Raises:
        ValueError: If X is empty or contamination is out of valid range.

    Example:
        >>> import pandas as pd
        >>> X = pd.DataFrame({
        ...     "cpu_usage": [70, 75, 80, 95, 72],
        ...     "memory_usage": [60, 65, 68, 90, 62],
        ... })
        >>> model = train_isolation_forest(X)
        >>> predictions = model.predict(X)  # -1 for anomalies, 1 for normal
    """
    if X.empty:
        raise ValueError("Cannot train model on empty feature matrix")

    if not 0 < contamination <= 0.5:
        raise ValueError(
            f"Contamination must be in (0, 0.5], got {contamination}"
        )

    n_samples, n_features = X.shape
    logger.info(
        f"Training IsolationForest on {n_samples} samples with {n_features} features"
    )
    logger.info(
        f"Hyperparameters: contamination={contamination}, "
        f"n_estimators={n_estimators}, max_samples={max_samples}, "
        f"random_state={random_state}"
    )

    # Initialize model
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        max_samples=max_samples,
        random_state=random_state,
        n_jobs=-1,  # Use all CPU cores
        **kwargs,
    )

    # Train model
    logger.info("Fitting IsolationForest model...")
    model.fit(X)

    # Log training statistics
    logger.info("Model training completed successfully")
    logger.info(f"Model parameters: {model.get_params()}")

    # Get decision scores for training data
    anomaly_scores = model.decision_function(X)
    predictions = model.predict(X)

    n_anomalies = (predictions == -1).sum()
    anomaly_percentage = (n_anomalies / n_samples) * 100

    logger.info(
        f"Training set statistics:\n"
        f"  - Detected anomalies: {n_anomalies}/{n_samples} ({anomaly_percentage:.2f}%)\n"
        f"  - Mean anomaly score: {anomaly_scores.mean():.4f}\n"
        f"  - Std anomaly score: {anomaly_scores.std():.4f}\n"
        f"  - Min score: {anomaly_scores.min():.4f}\n"
        f"  - Max score: {anomaly_scores.max():.4f}"
    )

    return model


def get_model_metadata(model: IsolationForest, X: pd.DataFrame) -> Dict[str, Any]:
    """Extract metadata about the trained model.

    This is useful for logging, monitoring, and model registry.

    Args:
        model: Trained IsolationForest model.
        X: Feature matrix used for training.

    Returns:
        Dictionary with model metadata including:
        - n_samples: Number of training samples
        - n_features: Number of features
        - feature_names: List of feature column names
        - hyperparameters: Model hyperparameters
        - training_anomaly_rate: Percentage of anomalies in training data
    """
    predictions = model.predict(X)
    n_anomalies = (predictions == -1).sum()
    anomaly_rate = (n_anomalies / len(X)) * 100

    metadata = {
        "n_samples": len(X),
        "n_features": X.shape[1],
        "feature_names": list(X.columns),
        "hyperparameters": model.get_params(),
        "training_anomaly_rate": round(anomaly_rate, 2),
        "model_type": "IsolationForest",
    }

    logger.debug(f"Extracted model metadata: {metadata}")

    return metadata


def validate_model(model: IsolationForest, X_val: pd.DataFrame) -> Dict[str, float]:
    """Validate the model on a validation set.

    Args:
        model: Trained IsolationForest model.
        X_val: Validation feature matrix.

    Returns:
        Dictionary with validation metrics.
    """
    if X_val.empty:
        logger.warning("Empty validation set provided")
        return {}

    predictions = model.predict(X_val)
    anomaly_scores = model.decision_function(X_val)

    n_anomalies = (predictions == -1).sum()
    anomaly_rate = (n_anomalies / len(X_val)) * 100

    metrics = {
        "val_samples": len(X_val),
        "val_anomalies": int(n_anomalies),
        "val_anomaly_rate": round(anomaly_rate, 2),
        "val_mean_score": round(anomaly_scores.mean(), 4),
        "val_std_score": round(anomaly_scores.std(), 4),
    }

    logger.info(f"Validation metrics: {metrics}")

    return metrics
