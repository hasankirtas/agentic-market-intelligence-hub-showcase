"""
Report repository.
"""
from typing import Optional, List
from google.cloud.firestore import Query
from app.database.firestore_client import get_firestore_client
from models.report import Report
from datetime import datetime
from core.logger import setup_logger
from google.api_core.exceptions import NotFound

logger = setup_logger(__name__)


class ReportRepository:
    """
    Repository for report CRUD operations.
    """
    
    def __init__(self, firestore_client=None):
        """
        Initialize report repository.
        
        Args:
            firestore_client: Firestore Client instance (optional, uses singleton if not provided)
        """
        if firestore_client is not None:
            self.firestore = firestore_client
        else:
            # Fallback to singleton for backward compatibility
            from app.database.firestore_client import FirestoreClient
            self.firestore = FirestoreClient()
        self.collection_name = "reports"
    
    async def save_report(self, report: Report) -> Report:
        """
        Save report to Firestore.
        
        Args:
            report: Report model instance
        
        Returns:
            Saved Report
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                report.report_id
            )
            
            report_dict = report.model_dump()
            # Convert datetime to Firestore timestamp
            report_dict["generated_at"] = report.generated_at
            if report.email_sent_at:
                report_dict["email_sent_at"] = report.email_sent_at
            
            doc_ref.set(report_dict)
            
            logger.info(f"Saved report: {report.report_id} for user: {report.user_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to save report {report.report_id}: {e}")
            raise
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """
        Get report by ID.
        
        Args:
            report_id: Report identifier
        
        Returns:
            Report if found, None otherwise
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                report_id
            )
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.debug(f"Report not found: {report_id}")
                return None
            
            report_dict = doc.to_dict()
            return Report(**report_dict)
            
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            return None
    
    async def get_reports_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Report]:
        """
        Get reports by user ID, ordered by generated_at (newest first).
        
        Args:
            user_id: User identifier
            limit: Maximum number of reports to return
        
        Returns:
            List of Report instances
        """
        try:
            reports_ref = self.firestore.get_collection(self.collection_name)
            query = reports_ref.where("user_id", "==", user_id)\
                             .order_by("generated_at", direction=Query.DESCENDING)\
                             .limit(limit)
            
            reports = []
            for doc in query.stream():
                report_dict = doc.to_dict()
                reports.append(Report(**report_dict))
            
            logger.info(f"Retrieved {len(reports)} reports for user: {user_id}")
            return reports
            
        except Exception as e:
            logger.error(f"Failed to get reports for user {user_id}: {e}")
            return []
    
    async def get_reports_by_type(
        self,
        user_id: str,
        report_type: str,
        limit: int = 50
    ) -> List[Report]:
        """
        Get reports by user ID and report type.
        
        Args:
            user_id: User identifier
            report_type: Report type ('scheduled' or 'emergency')
            limit: Maximum number of reports to return
        
        Returns:
            List of Report instances
        """
        try:
            reports_ref = self.firestore.get_collection(self.collection_name)
            query = reports_ref.where("user_id", "==", user_id)\
                             .where("report_type", "==", report_type)\
                             .order_by("generated_at", direction=Query.DESCENDING)\
                             .limit(limit)
            
            reports = []
            for doc in query.stream():
                report_dict = doc.to_dict()
                reports.append(Report(**report_dict))
            
            logger.info(
                f"Retrieved {len(reports)} {report_type} reports for user: {user_id}"
            )
            return reports
            
        except Exception as e:
            logger.error(
                f"Failed to get {report_type} reports for user {user_id}: {e}"
            )
            return []
    
    async def get_latest_report(
        self,
        user_id: str,
        report_type: Optional[str] = None
    ) -> Optional[Report]:
        """
        Get the latest report for a user, optionally filtered by type.
        
        Args:
            user_id: User identifier
            report_type: Optional report type filter ('scheduled' or 'emergency')
        
        Returns:
            Latest Report if found, None otherwise
        """
        try:
            reports_ref = self.firestore.get_collection(self.collection_name)
            query = reports_ref.where("user_id", "==", user_id)
            
            if report_type:
                query = query.where("report_type", "==", report_type)
            
            query = query.order_by("generated_at", direction=Query.DESCENDING).limit(1)
            
            docs = list(query.stream())
            if not docs:
                logger.debug(f"No report found for user: {user_id}, type: {report_type}")
                return None
            
            report_dict = docs[0].to_dict()
            return Report(**report_dict)
            
        except Exception as e:
            logger.error(f"Failed to get latest report for user {user_id}: {e}")
            return None
    
    async def mark_email_sent(self, report_id: str) -> None:
        """
        Mark report as email sent.
        
        Args:
            report_id: Report identifier
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                report_id
            )
            
            doc_ref.update({
                "email_sent": True,
                "email_sent_at": datetime.utcnow()
            })
            
            logger.info(f"Marked report {report_id} as email sent")
            
        except Exception as e:
            logger.error(f"Failed to mark email sent for report {report_id}: {e}")
            raise

    async def delete_report(self, report_id: str) -> bool:
        """Delete a single report by ID."""
        try:
            doc_ref = self.firestore.get_document(self.collection_name, report_id)
            doc_ref.delete()
            logger.info(f"Deleted report: {report_id}")
            return True
        except NotFound:
            logger.warning(f"Report not found for delete: {report_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            return False

    async def delete_reports_by_user(
        self,
        user_id: str,
        report_ids: Optional[List[str]] = None
    ) -> int:
        """
        Delete reports for a user. If report_ids is provided, delete only those; otherwise delete all for the user.
        Returns count of deleted reports.
        """
        deleted = 0
        try:
            if report_ids:
                for rid in report_ids:
                    doc_ref = self.firestore.get_document(self.collection_name, rid)
                    doc = doc_ref.get()
                    if doc.exists and doc.to_dict().get("user_id") == user_id:
                        doc_ref.delete()
                        deleted += 1
                logger.info(f"Deleted {deleted} reports for user {user_id} (selected)")
                return deleted

            # delete all for user
            reports_ref = self.firestore.get_collection(self.collection_name)
            query = reports_ref.where("user_id", "==", user_id)
            for doc in query.stream():
                doc.reference.delete()
                deleted += 1
            logger.info(f"Deleted {deleted} reports for user {user_id} (all)")
            return deleted
        except Exception as e:
            logger.error(f"Failed bulk delete for user {user_id}: {e}")
            return deleted
