"""Actions logger for persisting action execution history.

This module provides logging functionality for remediation actions.
Currently logs to console, but designed with a stable interface for
easy BigQuery integration.
"""

import logging
import json
from typing import Optional
from datetime import datetime

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from libs.core.config import GCPConfig

# Import using dynamic loading
import importlib.util
models_path = Path(__file__).parent.parent / "domain" / "models.py"
models_spec = importlib.util.spec_from_file_location("models", models_path)
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
ActionRecord = models_module.ActionRecord

logger = logging.getLogger(__name__)


class ActionsLogger:
    """Logger for remediation action execution history.
    
    This class provides a stable interface for logging actions that can be
    backed by different storage mechanisms (console, BigQuery, etc.).
    
    Currently logs to console - ready for BigQuery integration without
    changing the public interface.
    """

    def __init__(
        self,
        config: Optional[GCPConfig] = None,
        backend: str = "console",
    ):
        """Initialize the actions logger.
        
        Args:
            config: GCP configuration (optional, required for BigQuery backend).
            backend: Storage backend ("console" or "bigquery").
        """
        self.config = config
        self.backend = backend
        
        if backend == "bigquery" and config:
            self.table_id = config.get_full_table_id(config.bigquery_table_actions)
            logger.info(f"Initialized ActionsLogger with BigQuery backend: {self.table_id}")
            
            # TODO: Initialize BigQuery client when ready
            # from google.cloud import bigquery
            # self.client = bigquery.Client(project=config.gcp_project_id)
        else:
            logger.info("Initialized ActionsLogger with console backend")

    def log_action(self, action: ActionRecord) -> None:
        """Log an action execution record.
        
        Args:
            action: ActionRecord to log.
            
        Raises:
            Exception: If logging fails (in future BigQuery implementation).
        """
        if self.backend == "bigquery":
            self._log_to_bigquery(action)
        else:
            self._log_to_console(action)

    def _log_to_console(self, action: ActionRecord) -> None:
        """Log action to console.
        
        Args:
            action: ActionRecord to log.
        """
        # Format as structured JSON log
        log_entry = {
            "timestamp": action.timestamp.isoformat(),
            "action_id": action.action_id,
            "action_type": action.action_type.value,
            "status": action.status.value,
            "service_name": action.service_name,
            "target_type": action.target_type.value,
            "cluster_name": action.cluster_name,
            "region": action.region,
            "namespace": action.namespace,
            "replicas": action.replicas,
            "min_replicas": action.min_replicas,
            "max_replicas": action.max_replicas,
            "reason": action.reason,
            "message": action.message,
        }
        
        # Log as INFO for successful actions, WARNING for failures
        log_level = logging.INFO if action.status.value == "success" else logging.WARNING
        
        logger.log(
            log_level,
            f"[ACTION LOG] {action.action_type.value} - {action.service_name}: {action.message}",
        )
        logger.debug(f"[ACTION DETAILS] {json.dumps(log_entry, indent=2)}")

    def _log_to_bigquery(self, action: ActionRecord) -> None:
        """Log action to BigQuery.
        
        Args:
            action: ActionRecord to log.
            
        Raises:
            Exception: If BigQuery insertion fails.
        """
        logger.info(
            f"[STUB] Would write action to BigQuery table {self.table_id}: "
            f"{action.action_id}"
        )
        
        # TODO: Implement actual BigQuery insertion
        # Example implementation:
        #
        # row_to_insert = action.to_dict()
        # 
        # errors = self.client.insert_rows_json(
        #     self.table_id,
        #     [row_to_insert]
        # )
        # 
        # if errors:
        #     logger.error(f"BigQuery insert errors: {errors}")
        #     raise Exception(f"Failed to insert action: {errors}")
        # 
        # logger.info(f"Action {action.action_id} logged to BigQuery")
        
        # Also log to console for visibility
        self._log_to_console(action)

    def get_actions_by_service(
        self,
        service_name: str,
        limit: int = 100,
    ) -> list:
        """Retrieve recent actions for a service.
        
        Args:
            service_name: Name of the service.
            limit: Maximum number of actions to retrieve.
            
        Returns:
            List of action records.
        """
        logger.info(
            f"[STUB] Would retrieve {limit} recent actions for service: {service_name}"
        )
        
        # TODO: Implement actual BigQuery query
        # Example implementation:
        #
        # query = f"""
        #     SELECT *
        #     FROM `{self.table_id}`
        #     WHERE service_name = @service_name
        #     ORDER BY timestamp DESC
        #     LIMIT @limit
        # """
        # 
        # job_config = bigquery.QueryJobConfig(
        #     query_parameters=[
        #         bigquery.ScalarQueryParameter("service_name", "STRING", service_name),
        #         bigquery.ScalarQueryParameter("limit", "INT64", limit),
        #     ]
        # )
        # 
        # query_job = self.client.query(query, job_config=job_config)
        # results = query_job.result()
        # 
        # return [dict(row) for row in results]
        
        return []

    def get_failed_actions(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> list:
        """Retrieve recent failed actions.
        
        Args:
            hours: Look back this many hours.
            limit: Maximum number of actions to retrieve.
            
        Returns:
            List of failed action records.
        """
        logger.info(
            f"[STUB] Would retrieve failed actions from last {hours} hours"
        )
        
        # TODO: Implement actual BigQuery query
        # Example implementation:
        #
        # from datetime import timedelta
        # 
        # lookback_time = datetime.utcnow() - timedelta(hours=hours)
        # 
        # query = f"""
        #     SELECT *
        #     FROM `{self.table_id}`
        #     WHERE status = 'failed'
        #       AND timestamp >= @lookback_time
        #     ORDER BY timestamp DESC
        #     LIMIT @limit
        # """
        # 
        # job_config = bigquery.QueryJobConfig(
        #     query_parameters=[
        #         bigquery.ScalarQueryParameter("lookback_time", "TIMESTAMP", lookback_time),
        #         bigquery.ScalarQueryParameter("limit", "INT64", limit),
        #     ]
        # )
        # 
        # query_job = self.client.query(query, job_config=job_config)
        # results = query_job.result()
        # 
        # return [dict(row) for row in results]
        
        return []
