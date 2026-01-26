"""
FastAPI dependencies.
"""
from typing import Optional
from fastapi import Depends
from app.core.orchestrator import get_orchestrator
from core.orchestration.orchestrator import Orchestrator as CoreOrchestrator
from app.database.firestore_client import FirestoreClient
from app.database.repositories.config_repository import ConfigRepository
from app.database.repositories.scan_repository import ScanRepository
from app.database.repositories.report_repository import ReportRepository
from app.services.email_service import EmailService
from app.services.scheduler_service import SchedulerService


# Global scheduler instance
_scheduler: Optional[SchedulerService] = None


def get_orchestrator_dependency() -> CoreOrchestrator:
    """
    FastAPI dependency for orchestrator.
    
    Returns:
        CoreOrchestrator instance
    """
    return get_orchestrator()


def get_firestore_client() -> FirestoreClient:
    """
    FastAPI dependency for Firestore client.
    
    Returns:
        FirestoreClient singleton instance
    """
    return FirestoreClient()


def get_config_repository(
    firestore_client: FirestoreClient = Depends(get_firestore_client)
) -> ConfigRepository:
    """
    FastAPI dependency for ConfigRepository.
    
    Args:
        firestore_client: Firestore client dependency
    
    Returns:
        ConfigRepository instance
    """
    # Repositories expect our FirestoreClient wrapper (has get_document/get_collection helpers)
    return ConfigRepository(firestore_client)


def get_scan_repository(
    firestore_client: FirestoreClient = Depends(get_firestore_client)
) -> ScanRepository:
    """
    FastAPI dependency for ScanRepository.
    
    Args:
        firestore_client: Firestore client dependency
    
    Returns:
        ScanRepository instance
    """
    return ScanRepository(firestore_client)


def get_report_repository(
    firestore_client: FirestoreClient = Depends(get_firestore_client)
) -> ReportRepository:
    """
    FastAPI dependency for ReportRepository.
    
    Args:
        firestore_client: Firestore client dependency
    
    Returns:
        ReportRepository instance
    """
    return ReportRepository(firestore_client)


def get_email_service(
    report_repository: ReportRepository = Depends(get_report_repository)
) -> EmailService:
    """
    FastAPI dependency for EmailService.
    
    Args:
        report_repository: ReportRepository dependency
    
    Returns:
        EmailService instance
    """
    return EmailService(report_repository=report_repository)


def get_scheduler() -> Optional[SchedulerService]:
    """
    Get the global scheduler instance.
    
    Returns:
        SchedulerService instance or None if not initialized
    """
    return _scheduler


def set_scheduler(scheduler: SchedulerService) -> None:
    """
    Set the global scheduler instance.
    
    Args:
        scheduler: SchedulerService instance
    """
    global _scheduler
    _scheduler = scheduler
