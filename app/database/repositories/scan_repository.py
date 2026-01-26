"""
Scan data repository with baseline management.
"""
from typing import Optional, List, Dict
import hashlib
from google.cloud.firestore import Query
from app.database.firestore_client import get_firestore_client
from models.scan_result import ScanResult
from datetime import datetime
from core.logger import setup_logger

logger = setup_logger(__name__)


class ScanRepository:
    """
    Repository for scan data CRUD operations and baseline management.
    Baseline storage: baselines/{user_id}/{url_hash}
    """
    
    def __init__(self, firestore_client=None):
        """
        Initialize scan repository.
        
        Args:
            firestore_client: Firestore Client instance (optional, uses singleton if not provided)
        """
        if firestore_client is not None:
            self.firestore = firestore_client
        else:
            # Fallback to singleton for backward compatibility
            from app.database.firestore_client import FirestoreClient
            self.firestore = FirestoreClient()
        self.scans_collection = "scans"
        self.baselines_collection = "baselines"
    
    def _hash_url(self, url: str) -> str:
        """
        Hash URL to create a safe document ID.
        
        Args:
            url: URL to hash
        
        Returns:
            Hashed URL string
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    async def save_scan(self, scan_result: ScanResult) -> ScanResult:
        """
        Save scan result to Firestore.
        Uses scan_id + url_hash as document ID to allow multiple URLs per scan_id.
        
        Args:
            scan_result: ScanResult model instance
        
        Returns:
            Saved ScanResult
        """
        try:
            # Create unique document ID: scan_id + url_hash
            # This allows multiple URLs to be saved for the same scan_id
            url_hash = self._hash_url(scan_result.url)
            doc_id = f"{scan_result.scan_id}_{url_hash}"
            
            doc_ref = self.firestore.get_document(
                self.scans_collection,
                doc_id
            )
            
            scan_dict = scan_result.model_dump()
            # Convert datetime to Firestore timestamp
            scan_dict["timestamp"] = scan_result.timestamp
            
            doc_ref.set(scan_dict)
            
            logger.info(f"Saved scan: {doc_id} (scan_id: {scan_result.scan_id}, url: {scan_result.url}) for user: {scan_result.user_id}")
            return scan_result
            
        except Exception as e:
            logger.error(f"Failed to save scan {scan_result.scan_id}: {e}")
            raise
    
    async def get_scan(self, scan_id: str) -> Optional[ScanResult]:
        """
        Get scan result by ID.
        
        Args:
            scan_id: Scan identifier
        
        Returns:
            ScanResult if found, None otherwise
        """
        try:
            doc_ref = self.firestore.get_document(
                self.scans_collection,
                scan_id
            )
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.debug(f"Scan not found: {scan_id}")
                return None
            
            scan_dict = doc.to_dict()
            return ScanResult(**scan_dict)
            
        except Exception as e:
            logger.error(f"Failed to get scan {scan_id}: {e}")
            return None
    
    async def get_scans_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[ScanResult]:
        """
        Get scans by user ID, ordered by timestamp (newest first).
        
        Args:
            user_id: User identifier
            limit: Maximum number of scans to return
        
        Returns:
            List of ScanResult instances
        """
        try:
            scans_ref = self.firestore.get_collection(self.scans_collection)
            query = scans_ref.where("user_id", "==", user_id)\
                            .order_by("timestamp", direction=Query.DESCENDING)\
                            .limit(limit)
            
            scans = []
            for doc in query.stream():
                scan_dict = doc.to_dict()
                scans.append(ScanResult(**scan_dict))
            
            logger.info(f"Retrieved {len(scans)} scans for user: {user_id}")
            return scans
            
        except Exception as e:
            logger.error(f"Failed to get scans for user {user_id}: {e}")
            return []
    
    async def get_latest_scan(
        self,
        url: str,
        user_id: str
    ) -> Optional[ScanResult]:
        """
        Get the latest successful scan for a URL and user.
        
        Args:
            url: URL to get scan for
            user_id: User identifier
        
        Returns:
            Latest ScanResult if found, None otherwise
        """
        try:
            scans_ref = self.firestore.get_collection(self.scans_collection)
            query = scans_ref.where("user_id", "==", user_id)\
                            .where("url", "==", url)\
                            .where("status", "==", "success")\
                            .order_by("timestamp", direction=Query.DESCENDING)\
                            .limit(1)
            
            docs = list(query.stream())
            if not docs:
                logger.debug(f"No successful scan found for URL: {url}, user: {user_id}")
                return None
            
            scan_dict = docs[0].to_dict()
            return ScanResult(**scan_dict)
            
        except Exception as e:
            logger.error(f"Failed to get latest scan for URL {url}: {e}")
            return None
    
    async def get_scans_since(
        self,
        user_id: str,
        since: datetime,
        limit: int = 1000
    ) -> List[ScanResult]:
        """
        Get all scans for a user since a specific timestamp.
        
        Used by report workflow to aggregate changes over a time period.
        
        Args:
            user_id: User identifier
            since: Get scans since this timestamp
            limit: Maximum number of scans to return (default: 1000)
        
        Returns:
            List of ScanResult instances ordered by timestamp (oldest first)
        """
        try:
            scans_ref = self.firestore.get_collection(self.scans_collection)
            query = scans_ref.where("user_id", "==", user_id)\
                            .where("timestamp", ">=", since)\
                            .order_by("timestamp", direction=Query.ASCENDING)\
                            .limit(limit)
            
            scans = []
            for doc in query.stream():
                scan_dict = doc.to_dict()
                scans.append(ScanResult(**scan_dict))
            
            logger.info(f"Retrieved {len(scans)} scans for user {user_id} since {since}")
            return scans
            
        except Exception as e:
            logger.error(f"Failed to get scans since {since} for user {user_id}: {e}")
            return []
    
    async def save_baseline(
        self,
        user_id: str,
        url: str,
        scan_data: Dict
    ) -> None:
        """
        Save baseline data for a URL.
        Path: baselines/{user_id}/{url_hash}
        
        Args:
            user_id: User identifier
            url: URL
            scan_data: Scan data to save as baseline
        """
        try:
            url_hash = self._hash_url(url)
            baseline_ref = self.firestore.get_document(
                self.baselines_collection,
                user_id
            )
            url_baseline_ref = baseline_ref.collection("urls").document(url_hash)
            
            baseline_dict = {
                "url": url,
                "url_hash": url_hash,
                "last_scan_data": scan_data,
                "last_scan_timestamp": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            url_baseline_ref.set(baseline_dict)
            
            logger.info(f"Saved baseline for URL: {url}, user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save baseline for URL {url}: {e}")
            raise
    
    async def get_baseline(
        self,
        user_id: str,
        url: str
    ) -> Optional[Dict]:
        """
        Get baseline data for a URL.
        
        Args:
            user_id: User identifier
            url: URL
        
        Returns:
            Baseline data dict if found, None otherwise
        """
        try:
            url_hash = self._hash_url(url)
            baseline_ref = self.firestore.get_document(
                self.baselines_collection,
                user_id
            )
            url_baseline_ref = baseline_ref.collection("urls").document(url_hash)
            doc = url_baseline_ref.get()
            
            if not doc.exists:
                logger.debug(f"Baseline not found for URL: {url}, user: {user_id}")
                return None
            
            baseline_dict = doc.to_dict()
            return baseline_dict.get("last_scan_data")
            
        except Exception as e:
            logger.error(f"Failed to get baseline for URL {url}: {e}")
            return None
    
    async def update_baseline(
        self,
        user_id: str,
        url: str,
        scan_data: Dict
    ) -> None:
        """
        Update baseline data for a URL.
        
        Args:
            user_id: User identifier
            url: URL
            scan_data: New scan data to update baseline
        """
        try:
            url_hash = self._hash_url(url)
            baseline_ref = self.firestore.get_document(
                self.baselines_collection,
                user_id
            )
            url_baseline_ref = baseline_ref.collection("urls").document(url_hash)
            
            update_dict = {
                "last_scan_data": scan_data,
                "last_scan_timestamp": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            url_baseline_ref.update(update_dict)
            
            logger.info(f"Updated baseline for URL: {url}, user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update baseline for URL {url}: {e}")
            raise
