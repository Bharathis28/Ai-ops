"""BigQuery writer for persisting metrics and logs.

This module provides writer classes for storing data in BigQuery.
Currently implemented as stubs with TODO comments for actual BigQuery integration.
"""

import logging
from typing import List

from libs.core.config import GCPConfig
from libs.models.metrics import MetricPoint
from services.ingestion-api.domain.models import LogEntry

logger = logging.getLogger(__name__)


class BigQueryMetricsWriter:
    """Writer class for persisting metrics to BigQuery.
    
    This class provides a stable interface for writing metrics to BigQuery.
    Future implementation will add actual BigQuery client integration without
    changing the public method signatures.
    """

    def __init__(self, config: GCPConfig):
        """Initialize the BigQuery metrics writer.
        
        Args:
            config: GCP configuration containing project ID, dataset, and table names.
        """
        self.config = config
        self.table_id = config.get_full_table_id(config.bigquery_table_metrics_raw)
        logger.info(f"Initialized BigQueryMetricsWriter for table: {self.table_id}")
        
        # Phase 8: Initialize BigQuery client
        from google.cloud import bigquery
        self.client = bigquery.Client(project=config.gcp_project_id)

    def write_metrics(self, metrics: List[MetricPoint]) -> None:
        """Write a batch of metrics to BigQuery.
        
        Args:
            metrics: List of MetricPoint objects to write.
            
        Raises:
            Exception: If writing to BigQuery fails (in future implementation).
        """
        if not metrics:
            logger.warning("Attempted to write empty metrics list to BigQuery")
            return

        # Phase 8: Implement actual BigQuery insertion
        import json
        
        rows_to_insert = [
            {
                "timestamp": metric.timestamp.isoformat(),
                "service_name": metric.service_name,
                "metric_name": metric.metric_name,
                "value": metric.value,
                "tags": json.dumps(metric.tags) if metric.tags else "{}",
            }
            for metric in metrics
        ]
        
        errors = self.client.insert_rows_json(self.table_id, rows_to_insert)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert metrics: {errors}")
        
        logger.info(
            f"Successfully wrote {len(metrics)} metrics to BigQuery table {self.table_id}"
        )
        logger.debug(f"Sample metric: {metrics[0].model_dump_json()}")

    def close(self) -> None:
        """Close the BigQuery client connection.
        
        This method is a placeholder for future cleanup operations.
        """
        # Phase 8: Close BigQuery client
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("BigQuery client closed")


class BigQueryLogsWriter:
    """Writer class for persisting logs to BigQuery.
    
    This class provides a stable interface for writing logs to BigQuery.
    Future implementation will add actual BigQuery client integration without
    changing the public method signatures.
    """

    def __init__(self, config: GCPConfig):
        """Initialize the BigQuery logs writer.
        
        Args:
            config: GCP configuration containing project ID, dataset, and table names.
        """
        self.config = config
        self.table_id = config.get_full_table_id(config.bigquery_table_logs_clean)
        logger.info(f"Initialized BigQueryLogsWriter for table: {self.table_id}")
        
        # Phase 8: Initialize BigQuery client
        from google.cloud import bigquery
        self.client = bigquery.Client(project=config.gcp_project_id)

    def write_logs(self, logs: List[LogEntry]) -> None:
        """Write a batch of log entries to BigQuery.
        
        Args:
            logs: List of LogEntry objects to write.
            
        Raises:
            Exception: If writing to BigQuery fails (in future implementation).
        """
        if not logs:
            logger.warning("Attempted to write empty logs list to BigQuery")
            return

        # Phase 8: Implement actual BigQuery insertion
        import json
        
        rows_to_insert = [
            {
                "timestamp": log.timestamp.isoformat(),
                "service_name": log.service_name,
                "level": log.level,
                "message": log.message,
                "metadata": json.dumps(log.metadata) if log.metadata else "{}",
            }
            for log in logs
        ]
        
        errors = self.client.insert_rows_json(self.table_id, rows_to_insert)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert logs: {errors}")
        
        logger.info(
            f"Successfully wrote {len(logs)} log entries to BigQuery table {self.table_id}"
        )
        logger.debug(f"Sample log: {logs[0].model_dump_json()}")

    def close(self) -> None:
        """Close the BigQuery client connection.
        
        This method is a placeholder for future cleanup operations.
        """
        # Phase 8: Close BigQuery client
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("BigQuery logs client closed")
