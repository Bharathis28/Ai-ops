"""Model storage for persisting trained models.

This module provides a ModelStore class for saving and loading trained models.
Currently implemented with local filesystem storage, but designed with a stable
interface for easy GCS integration later.
"""

import logging
import pickle
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from sklearn.base import BaseEstimator

logger = logging.getLogger(__name__)


class ModelStore:
    """Storage backend for machine learning models.

    Public interface is stable - implementation can switch from local filesystem
    to GCS without changing callers.

    Args:
        base_path: Base directory for model storage. For local filesystem, this is
            a local path. For GCS, this would be a bucket name (e.g., "gs://my-bucket/models").
        backend: Storage backend type. Currently only "local" is implemented.
            Future: "gcs" for Google Cloud Storage.
    """

    def __init__(
        self,
        base_path: str = "./models",
        backend: str = "local",
    ):
        """Initialize the model store.

        Args:
            base_path: Base path for storing models.
            backend: Storage backend ("local" or "gcs").
        """
        self.base_path = base_path
        self.backend = backend

        if backend == "local":
            self._init_local_storage()
        elif backend == "gcs":
            # TODO: Implement GCS storage
            raise NotImplementedError(
                "GCS backend not yet implemented. Use backend='local' for now."
            )
        else:
            raise ValueError(f"Unknown backend: {backend}. Must be 'local' or 'gcs'.")

        logger.info(f"Initialized ModelStore with backend={backend}, base_path={base_path}")

    def _init_local_storage(self) -> None:
        """Initialize local filesystem storage."""
        # Create base directory if it doesn't exist
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Local storage initialized at: {self.base_path}")

    def save_model(
        self,
        service_name: str,
        model: BaseEstimator,
        metadata: Optional[dict] = None,
        version: Optional[str] = None,
    ) -> str:
        """Save a trained model.

        Args:
            service_name: Name of the service the model is for (e.g., "frontend-api").
            model: Trained scikit-learn model (must be picklable).
            metadata: Optional metadata dictionary to save alongside the model.
            version: Optional version string. If None, uses timestamp.

        Returns:
            Path where the model was saved.

        Raises:
            ValueError: If service_name is empty or model is None.
            IOError: If saving fails.

        Example:
            >>> from sklearn.ensemble import IsolationForest
            >>> model = IsolationForest()
            >>> store = ModelStore(base_path="./models")
            >>> path = store.save_model("frontend-api", model, metadata={"n_samples": 1000})
            >>> print(path)
            ./models/frontend-api/model.pkl
        """
        if not service_name:
            raise ValueError("service_name cannot be empty")

        if model is None:
            raise ValueError("model cannot be None")

        # Generate version if not provided
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Saving model for service: {service_name}, version: {version}")

        if self.backend == "local":
            return self._save_model_local(service_name, model, metadata, version)
        elif self.backend == "gcs":
            # TODO: Implement GCS save
            return self._save_model_gcs(service_name, model, metadata, version)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _save_model_local(
        self,
        service_name: str,
        model: BaseEstimator,
        metadata: Optional[dict],
        version: str,
    ) -> str:
        """Save model to local filesystem.

        Args:
            service_name: Service name.
            model: Trained model.
            metadata: Optional metadata.
            version: Version string.

        Returns:
            Path to saved model.
        """
        # Create service directory
        service_dir = Path(self.base_path) / service_name
        service_dir.mkdir(parents=True, exist_ok=True)

        # Save model
        model_path = service_dir / "model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        logger.info(f"Model saved to: {model_path}")

        # Save metadata if provided
        if metadata is not None:
            metadata_path = service_dir / "metadata.pkl"
            with open(metadata_path, "wb") as f:
                pickle.dump(metadata, f)
            logger.info(f"Metadata saved to: {metadata_path}")

        # Save version info
        version_path = service_dir / "version.txt"
        with open(version_path, "w") as f:
            f.write(version)
        logger.debug(f"Version saved to: {version_path}")

        return str(model_path)

    def _save_model_gcs(
        self,
        service_name: str,
        model: BaseEstimator,
        metadata: Optional[dict],
        version: str,
    ) -> str:
        """Save model to Google Cloud Storage.

        TODO: Implement this when GCS integration is ready.

        Example implementation:
        ```python
        from google.cloud import storage
        import io

        # Serialize model to bytes
        model_bytes = pickle.dumps(model)

        # Upload to GCS
        bucket_name = self.base_path.replace("gs://", "").split("/")[0]
        blob_path = f"models/{service_name}/model.pkl"

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(model_bytes)

        return f"gs://{bucket_name}/{blob_path}"
        ```
        """
        raise NotImplementedError("GCS backend not yet implemented")

    def load_model(self, service_name: str) -> BaseEstimator:
        """Load a trained model.

        Args:
            service_name: Name of the service.

        Returns:
            Loaded scikit-learn model.

        Raises:
            FileNotFoundError: If model doesn't exist.
            IOError: If loading fails.
        """
        if not service_name:
            raise ValueError("service_name cannot be empty")

        logger.info(f"Loading model for service: {service_name}")

        if self.backend == "local":
            return self._load_model_local(service_name)
        elif self.backend == "gcs":
            return self._load_model_gcs(service_name)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _load_model_local(self, service_name: str) -> BaseEstimator:
        """Load model from local filesystem."""
        model_path = Path(self.base_path) / service_name / "model.pkl"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found for service: {service_name} at {model_path}"
            )

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        logger.info(f"Model loaded from: {model_path}")

        return model

    def _load_model_gcs(self, service_name: str) -> BaseEstimator:
        """Load model from Google Cloud Storage."""
        raise NotImplementedError("GCS backend not yet implemented")

    def load_metadata(self, service_name: str) -> Optional[dict]:
        """Load model metadata.

        Args:
            service_name: Name of the service.

        Returns:
            Metadata dictionary, or None if not found.
        """
        if self.backend == "local":
            metadata_path = Path(self.base_path) / service_name / "metadata.pkl"

            if not metadata_path.exists():
                logger.warning(f"Metadata not found for service: {service_name}")
                return None

            with open(metadata_path, "rb") as f:
                metadata = pickle.load(f)

            logger.info(f"Metadata loaded from: {metadata_path}")
            return metadata

        elif self.backend == "gcs":
            raise NotImplementedError("GCS backend not yet implemented")

        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def model_exists(self, service_name: str) -> bool:
        """Check if a model exists for the given service.

        Args:
            service_name: Name of the service.

        Returns:
            True if model exists, False otherwise.
        """
        if self.backend == "local":
            model_path = Path(self.base_path) / service_name / "model.pkl"
            return model_path.exists()
        elif self.backend == "gcs":
            raise NotImplementedError("GCS backend not yet implemented")
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
