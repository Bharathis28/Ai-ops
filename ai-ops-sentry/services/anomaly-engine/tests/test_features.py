"""Unit tests for feature engineering."""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import using dynamic loading
import importlib.util

features_path = Path(__file__).parent.parent / "domain" / "features.py"
features_spec = importlib.util.spec_from_file_location("features", features_path)
features_module = importlib.util.module_from_spec(features_spec)
features_spec.loader.exec_module(features_module)
build_feature_matrix = features_module.build_feature_matrix
add_time_features = features_module.add_time_features
METRIC_COLUMNS = features_module.METRIC_COLUMNS


class TestBuildFeatureMatrix(unittest.TestCase):
    """Test cases for build_feature_matrix function."""

    def setUp(self):
        """Set up test data."""
        self.df = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=10, freq="1h"),
            "service_name": ["api"] * 10,
            "cpu_usage": [70, 75, 80, 85, 90, 95, 72, 68, 73, 78],
            "memory_usage": [60, 65, 70, 75, 80, 85, 62, 58, 63, 68],
            "latency_p95": [100, 110, 120, 130, 140, 150, 105, 95, 100, 115],
            "request_rate": [1000, 1100, 1200, 1300, 1400, 1500, 1050, 950, 1000, 1100],
            "error_rate": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.6, 0.4, 0.5, 0.6],
        })

    def test_basic_functionality(self):
        """Test basic feature matrix creation."""
        X = build_feature_matrix(self.df)

        # Check shape
        self.assertEqual(X.shape[0], 10)
        self.assertEqual(X.shape[1], 5)

        # Check columns
        self.assertListEqual(list(X.columns), METRIC_COLUMNS)

        # Check no missing values
        self.assertFalse(X.isnull().any().any())

    def test_custom_columns(self):
        """Test with custom feature columns."""
        custom_cols = ["cpu_usage", "memory_usage"]
        X = build_feature_matrix(self.df, feature_columns=custom_cols)

        self.assertEqual(X.shape[1], 2)
        self.assertListEqual(list(X.columns), custom_cols)

    def test_missing_columns_raises_error(self):
        """Test that missing columns raise ValueError."""
        with self.assertRaises(ValueError) as context:
            build_feature_matrix(self.df, feature_columns=["nonexistent_column"])

        self.assertIn("missing from DataFrame", str(context.exception))

    def test_handle_missing_values_median(self):
        """Test median strategy for missing values."""
        df_with_missing = self.df.copy()
        df_with_missing.loc[0, "cpu_usage"] = np.nan
        df_with_missing.loc[1, "memory_usage"] = np.nan

        X = build_feature_matrix(df_with_missing, fill_strategy="median")

        # Should have no missing values
        self.assertFalse(X.isnull().any().any())

        # Check that the filled values are reasonable (non-zero, within normal range)
        self.assertGreater(X.iloc[0]["cpu_usage"], 0)
        self.assertLess(X.iloc[0]["cpu_usage"], 100)

    def test_handle_missing_values_mean(self):
        """Test mean strategy for missing values."""
        df_with_missing = self.df.copy()
        df_with_missing.loc[0, "cpu_usage"] = np.nan

        X = build_feature_matrix(df_with_missing, fill_strategy="mean")

        # Should have no missing values
        self.assertFalse(X.isnull().any().any())

    def test_handle_missing_values_zero(self):
        """Test zero fill strategy."""
        df_with_missing = self.df.copy()
        df_with_missing.loc[0, "cpu_usage"] = np.nan

        X = build_feature_matrix(df_with_missing, fill_strategy="zero")

        self.assertEqual(X.iloc[0]["cpu_usage"], 0.0)

    def test_handle_missing_values_drop(self):
        """Test drop strategy for missing values."""
        df_with_missing = self.df.copy()
        df_with_missing.loc[0, "cpu_usage"] = np.nan
        df_with_missing.loc[1, "memory_usage"] = np.nan

        X = build_feature_matrix(df_with_missing, fill_strategy="drop")

        # Should have dropped rows with missing values
        self.assertEqual(len(X), 8)  # Original 10 - 2 dropped
        self.assertFalse(X.isnull().any().any())

    def test_invalid_fill_strategy(self):
        """Test that invalid fill strategy raises ValueError."""
        with self.assertRaises(ValueError) as context:
            build_feature_matrix(self.df, fill_strategy="invalid")

        self.assertIn("Invalid fill_strategy", str(context.exception))

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pd.DataFrame()
        X = build_feature_matrix(empty_df)

        self.assertTrue(X.empty)

    def test_all_missing_values(self):
        """Test with all values missing in a column."""
        df_all_missing = self.df.copy()
        df_all_missing["cpu_usage"] = np.nan

        # Median/mean will be NaN, should raise error
        with self.assertRaises(ValueError):
            build_feature_matrix(df_all_missing, fill_strategy="median")


class TestAddTimeFeatures(unittest.TestCase):
    """Test cases for add_time_features function."""

    def test_add_time_features(self):
        """Test adding time-based features."""
        df = pd.DataFrame({
            "timestamp": pd.date_range("2025-01-01", periods=24, freq="1h"),
            "value": range(24),
        })

        df_with_time = add_time_features(df, timestamp_col="timestamp")

        # Check new columns exist
        self.assertIn("hour", df_with_time.columns)
        self.assertIn("day_of_week", df_with_time.columns)
        self.assertIn("is_weekend", df_with_time.columns)

        # Check hour values
        self.assertEqual(df_with_time["hour"].min(), 0)
        self.assertEqual(df_with_time["hour"].max(), 23)

        # Check day of week (2025-01-01 is Wednesday = 2)
        self.assertEqual(df_with_time["day_of_week"].iloc[0], 2)

    def test_missing_timestamp_column(self):
        """Test when timestamp column is missing."""
        df = pd.DataFrame({"value": [1, 2, 3]})

        df_result = add_time_features(df, timestamp_col="nonexistent")

        # Should return original df
        self.assertEqual(len(df_result.columns), 1)


if __name__ == "__main__":
    unittest.main()
