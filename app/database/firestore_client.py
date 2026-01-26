"""
Firestore client wrapper.
Uses Application Default Credentials (ADC) for authentication.
"""
from google.cloud import firestore
from google.cloud.firestore import Client
from typing import Optional
import os
from core.logger import setup_logger

logger = setup_logger(__name__)


class FirestoreClient:
    """
    Singleton Firestore client wrapper.
    Uses Application Default Credentials (ADC) for authentication.
    
    Local development: gcloud auth application-default login
    Production: Automatically uses service account from environment
    """
    _instance: Optional['FirestoreClient'] = None
    _client: Optional[Client] = None

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Firestore client if not already initialized."""
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Firestore client with ADC."""
        try:
            # Use Application Default Credentials
            # Local: gcloud auth application-default login
            # Production: Automatically uses service account
            self._client = firestore.Client()
            logger.info("Firestore client initialized with ADC")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    @property
    def client(self) -> Client:
        """Get Firestore client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client

    def get_collection(self, collection_path: str):
        """
        Get a Firestore collection reference.
        
        Args:
            collection_path: Collection path (e.g., 'users', 'scans')
        
        Returns:
            Collection reference
        """
        return self.client.collection(collection_path)

    def get_document(self, collection_path: str, document_id: str):
        """
        Get a Firestore document reference.
        
        Args:
            collection_path: Collection path
            document_id: Document ID
        
        Returns:
            Document reference
        """
        return self.client.collection(collection_path).document(document_id)

    def batch(self):
        """
        Create a Firestore batch for batch operations.
        
        Returns:
            Batch object
        """
        return self.client.batch()

    def close(self):
        """Close Firestore client connection."""
        if self._client:
            # Firestore client doesn't have explicit close, but we can reset
            self._client = None
            logger.info("Firestore client closed")


# Singleton instance getter
def get_firestore_client() -> FirestoreClient:
    """
    Get singleton Firestore client instance.
    
    Returns:
        FirestoreClient instance
    """
    return FirestoreClient()
