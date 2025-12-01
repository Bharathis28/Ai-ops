"""Writer for persisting anomaly detection results.

This module provides an interface and implementations for writing
anomaly detection results to storage (BigQuery).
"""

import logging
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from libs.core.config import GCPConfig

# Import using sys.path to handle hyphenated directory
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import importlib.util
scoring_path = Path(__file__).parent.parent / "domain" / "scoring.py"
scoring_spec = importlib.util.spec_from_file_location("scoring", scoring_path)
scoring_module = importlib.util.module_from_spec(scoring_spec)
scoring_spec.loader.exec_module(scoring_module)
AnomalyResult = scoring_module.AnomalyResult

logger = logging.getLogger(__name__)


class AnomalyWriter(ABC):
    """Abstract interface for writing anomaly detection results.

    This interface allows different backend implementations (BigQuery, local file, etc.)
    without changing the scoring logic.
    """

    @abstractmethod
    def write_anomalies(self, anomalies: List[AnomalyResult]) -> None:
        """Write a batch of anomaly results.

        Args:
            anomalies: List of AnomalyResult objects to write.

        Raises:
            Exception: If writing fails.
        """
        pass


class BigQueryAnomalyWriter(AnomalyWriter):
    """BigQuery implementation of AnomalyWriter.

    Currently stubbed - logs anomalies instead of writing to BigQuery.
    Ready for BigQuery integration without changing the public interface.
    """

    def __init__(self, config: GCPConfig):
        """Initialize the BigQuery anomaly writer.

        Args:
            config: GCP configuration containing project ID, dataset, and table names.
        """
        self.config = config
        self.table_id = config.get_full_table_id(config.bigquery_table_anomalies)
        logger.info(f"Initialized BigQueryAnomalyWriter for table: {self.table_id}")

        # Initialize BigQuery client
        if config.enable_gcp_clients:
            from google.cloud import bigquery
            self.client = bigquery.Client(project=config.gcp_project_id)
        else:
            self.client = None
            logger.warning("GCP clients disabled, BigQuery writes will be skipped")

    def write_anomalies(self, anomalies: List[AnomalyResult]) -> None:
        """Write anomalies to BigQuery.

        Args:
            anomalies: List of AnomalyResult objects to write.

        Raises:
            Exception: If writing to BigQuery fails (in future implementation).
        """
        if not anomalies:
            logger.warning("Attempted to write empty anomalies list")
            return

        if self.client is None:
            logger.info(f"[STUB] GCP clients disabled. Would write {len(anomalies)} anomalies to BigQuery")
            for anomaly in anomalies:
                logger.debug(
                    f"[STUB] Anomaly: {anomaly.service_name}/{anomaly.metric_name} = {anomaly.value} "
                    f"(severity: {anomaly.severity}, score: {anomaly.anomaly_score:.4f})"
                )
            return

        # Actual BigQuery insertion
        import json
        
        rows_to_insert = []
        for anomaly in anomalies:
            # Map AnomalyResult fields to BigQuery schema
            row = {
                "timestamp": anomaly.timestamp.isoformat(),
                "service_name": anomaly.service_name,
                "metric_name": anomaly.metric_name,
                "anomaly_score": anomaly.anomaly_score,
                "expected_value": anomaly.metadata.get("expected_value", 0.0),
                "actual_value": anomaly.value,
                "severity": anomaly.severity,
                "description": f"Anomaly detected: {anomaly.metric_name} = {anomaly.value:.2f} (score: {anomaly.anomaly_score:.4f})",
            }
            rows_to_insert.append(row)

        try:
            errors = self.client.insert_rows_json(self.table_id, rows_to_insert)
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                raise Exception(f"Failed to insert anomalies: {errors}")
            
            logger.info(f"Successfully wrote {len(anomalies)} anomalies to BigQuery table {self.table_id}")
            logger.debug(f"Sample anomaly: {anomalies[0].to_dict()}")
        except Exception as e:
            logger.error(f"Failed to write anomalies to BigQuery: {e}")
            raise


class LocalFileAnomalyWriter(AnomalyWriter):
    """Local file implementation of AnomalyWriter for testing.

    Writes anomalies to a local JSON file.
    """

    def __init__(self, output_file: str = "./anomalies.jsonl"):
        """Initialize the local file writer.

        Args:
            output_file: Path to output file (JSONL format).
        """
        self.output_file = output_file
        logger.info(f"Initialized LocalFileAnomalyWriter: {output_file}")

    def write_anomalies(self, anomalies: List[AnomalyResult]) -> None:
        """Write anomalies to local file.

        Args:
            anomalies: List of AnomalyResult objects to write.
        """
        if not anomalies:
            return

        import json

        with open(self.output_file, "a") as f:
            for anomaly in anomalies:
                f.write(json.dumps(anomaly.to_dict()) + "\n")

        logger.info(f"Wrote {len(anomalies)} anomalies to {self.output_file}")
