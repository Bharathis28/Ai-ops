"""Feature engineering for anomaly detection.

This module provides functions to transform raw metrics data into
feature matrices suitable for machine learning models.
"""

import logging
from typing import List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Standard metric columns expected in the dataset
METRIC_COLUMNS = [
    "cpu_usage",
    "memory_usage",
    "latency_p95",
    "request_rate",
    "error_rate",
]


def build_feature_matrix(
    df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    fill_strategy: str = "median",
) -> pd.DataFrame:
    """Build a feature matrix from raw metrics data.

    This function selects numeric columns, handles missing values, and prepares
    the data for model training. The public interface is stable - internal
    implementation can be enhanced without breaking callers.

    Args:
        df: Raw metrics DataFrame with timestamp, service_name, and metric columns.
        feature_columns: List of columns to use as features. If None, uses METRIC_COLUMNS.
        fill_strategy: Strategy for handling missing values. Options:
            - "median": Fill with median value per column
            - "mean": Fill with mean value per column
            - "zero": Fill with zeros
            - "drop": Drop rows with any missing values

    Returns:
        DataFrame with selected feature columns, missing values handled.

    Raises:
        ValueError: If required columns are missing or fill_strategy is invalid.

    Example:
        >>> df = pd.DataFrame({
        ...     "timestamp": ["2025-01-01", "2025-01-02"],
        ...     "service_name": ["api", "api"],
        ...     "cpu_usage": [75.5, 80.2],
        ...     "memory_usage": [60.0, None],
        ...     "latency_p95": [120.0, 150.0],
        ... })
        >>> features = build_feature_matrix(df)
        >>> features.shape
        (2, 3)
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to build_feature_matrix")
        return pd.DataFrame()

    # Use default columns if not specified
    if feature_columns is None:
        feature_columns = METRIC_COLUMNS

    # Validate columns exist
    missing_cols = [col for col in feature_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Required columns missing from DataFrame: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    # Select feature columns
    X = df[feature_columns].copy()

    # Log initial state
    total_missing = X.isnull().sum().sum()
    if total_missing > 0:
        logger.info(
            f"Found {total_missing} missing values across {len(feature_columns)} features"
        )
        logger.debug(f"Missing values per column:\n{X.isnull().sum()}")

    # Handle missing values based on strategy
    if fill_strategy == "median":
        for col in feature_columns:
            if X[col].isnull().any():
                median_val = X[col].median()
                X[col].fillna(median_val, inplace=True)
                logger.debug(f"Filled {col} missing values with median: {median_val:.2f}")

    elif fill_strategy == "mean":
        for col in feature_columns:
            if X[col].isnull().any():
                mean_val = X[col].mean()
                X[col].fillna(mean_val, inplace=True)
                logger.debug(f"Filled {col} missing values with mean: {mean_val:.2f}")

    elif fill_strategy == "zero":
        X.fillna(0, inplace=True)
        logger.debug("Filled all missing values with zeros")

    elif fill_strategy == "drop":
        rows_before = len(X)
        X.dropna(inplace=True)
        rows_after = len(X)
        if rows_before > rows_after:
            logger.info(f"Dropped {rows_before - rows_after} rows with missing values")

    else:
        raise ValueError(
            f"Invalid fill_strategy: {fill_strategy}. "
            f"Must be one of: median, mean, zero, drop"
        )

    # Validate output
    if X.isnull().any().any():
        logger.error("Feature matrix still contains missing values after processing")
        raise ValueError("Failed to handle all missing values")

    logger.info(
        f"Built feature matrix: {X.shape[0]} samples × {X.shape[1]} features"
    )

    return X


def add_time_features(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Add time-based features to the dataset.

    This is a helper function for future enhancement. Can add hour of day,
    day of week, etc. for more sophisticated anomaly detection.

    Args:
        df: DataFrame with timestamp column.
        timestamp_col: Name of the timestamp column.

    Returns:
        DataFrame with additional time-based features.
    """
    df = df.copy()

    if timestamp_col not in df.columns:
        logger.warning(f"Timestamp column '{timestamp_col}' not found, skipping time features")
        return df

    # Convert to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Extract time features
    df["hour"] = df[timestamp_col].dt.hour
    df["day_of_week"] = df[timestamp_col].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    logger.debug("Added time features: hour, day_of_week, is_weekend")

    return df


def normalize_features(X: pd.DataFrame) -> pd.DataFrame:
    """Normalize features to zero mean and unit variance.

    Note: IsolationForest doesn't require normalization, but this function
    is provided for future use with other algorithms.

    Args:
        X: Feature matrix to normalize.

    Returns:
        Normalized feature matrix.
    """
    X_normalized = (X - X.mean()) / X.std()
    logger.debug("Normalized features to zero mean and unit variance")
    return X_normalized
