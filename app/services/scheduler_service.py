"""
Job scheduling service.

Manages scheduled job execution using APScheduler for automated
competitive intelligence monitoring workflows.

Uses config-driven scheduling: scan frequency and report frequency
are defined in user configuration.
"""
from typing import Optional, Any
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from core.logger import setup_logger
from workflows.scan_workflow import execute_scan_workflow
from workflows.report_workflow import execute_report_workflow
from models.config import UserConfig

logger = setup_logger(__name__)


class SchedulerService:
    """
    Scheduler service for managing automated workflow execution.
    
    Uses APScheduler AsyncIOScheduler for non-blocking job execution.
    Supports config-driven scheduling based on user configuration.
    
    Attributes:
        user_id: User identifier for scheduled workflows
        scheduler: APScheduler instance
        watcher_agent: Watcher agent instance
        analyst_agent: Analyst agent instance
        reporter_agent: Reporter agent instance
        email_service: Email service instance
        config_repository: Config repository instance
        scan_repository: Scan repository instance
        report_repository: Report repository instance
    """
    
    def __init__(
        self,
        user_id: str,
        watcher_agent: Any,
        analyst_agent: Any,
        reporter_agent: Any,
        email_service: Any,
        config_repository: Any,
        scan_repository: Any,
        report_repository: Any,
        timezone: str = "UTC"
    ):
        """
        Initialize scheduler service.
        
        Args:
            user_id: User identifier
            watcher_agent: Watcher agent instance
            analyst_agent: Analyst agent instance
            reporter_agent: Reporter agent instance
            email_service: Email service instance
            config_repository: Config repository instance
            scan_repository: Scan repository instance
            report_repository: Report repository instance
            timezone: Timezone for scheduling (default: UTC)
        """
        self.user_id = user_id
        self.watcher_agent = watcher_agent
        self.analyst_agent = analyst_agent
        self.reporter_agent = reporter_agent
        self.email_service = email_service
        self.config_repository = config_repository
        self.scan_repository = scan_repository
        self.report_repository = report_repository
        
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info(f"SchedulerService initialized for user: {user_id}")
    
    async def start(self, user_config: UserConfig) -> None:
        """
        Start the scheduler and register jobs based on user configuration.
        
        Args:
            user_config: User configuration with scan and report schedules
        """
        # Register scan job (frequent - e.g., every hour)
        scan_trigger = CronTrigger.from_crontab(user_config.scan_schedule)
        self.scheduler.add_job(
            func=self._execute_scan_job,
            trigger=scan_trigger,
            id='scan_job',
            name=f'Scan job for user {self.user_id}',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        
        logger.info(f"Scan job scheduled: {user_config.scan_schedule}")
        
        # Register report job (less frequent - e.g., every 6 hours)
        report_trigger = CronTrigger.from_crontab(user_config.report_schedule)
        self.scheduler.add_job(
            func=self._execute_report_job,
            trigger=report_trigger,
            id='report_job',
            name=f'Report job for user {self.user_id}',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )
        
        logger.info(f"Report job scheduled: {user_config.report_schedule}")
        
        # Start scheduler
        self.scheduler.start()
        
        logger.info(
            f"Scheduler started with scan schedule: {user_config.scan_schedule}, "
            f"report schedule: {user_config.report_schedule}"
        )
    
    async def _execute_scan_job(self) -> None:
        """
        Execute scan job workflow.
        
        Scans URLs, detects changes, and sends emergency email if threshold exceeded.
        """
        logger.info(f"Starting scan job for user: {self.user_id}")
        
        try:
            result = await execute_scan_workflow(
                user_id=self.user_id,
                watcher_agent=self.watcher_agent,
                analyst_agent=self.analyst_agent,
                config_repository=self.config_repository,
                scan_repository=self.scan_repository,
                email_service=self.email_service
            )
            
            if result.get("success"):
                logger.info(
                    f"Scan job completed: "
                    f"changes={result.get('change_count')}, "
                    f"emergency={result.get('is_emergency')}, "
                    f"execution_time={result.get('execution_time'):.2f}s"
                )
            else:
                logger.error(f"Scan job failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Scan job failed with exception: {e}", exc_info=True)
    
    async def _execute_report_job(self) -> None:
        """
        Execute report job workflow.
        
        Aggregates recent scans, generates summary report, and sends scheduled email.
        """
        logger.info(f"Starting report job for user: {self.user_id}")
        
        try:
            result = await execute_report_workflow(
                user_id=self.user_id,
                reporter_agent=self.reporter_agent,
                email_service=self.email_service,
                config_repository=self.config_repository,
                scan_repository=self.scan_repository,
                report_repository=self.report_repository
            )
            
            if result.get("success"):
                logger.info(
                    f"Report job completed: "
                    f"report_id={result.get('report_id')}, "
                    f"scans={result.get('scan_count')}, "
                    f"changes={result.get('change_count')}, "
                    f"execution_time={result.get('execution_time'):.2f}s"
                )
            else:
                logger.error(f"Report job failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Report job failed with exception: {e}", exc_info=True)
    
    def _job_listener(self, event) -> None:
        """
        Listen to job events for monitoring and logging.
        
        Args:
            event: APScheduler job event
        """
        if event.exception:
            logger.error(
                f"Job {event.job_id} failed with exception: {event.exception}"
            )
        else:
            logger.debug(f"Job {event.job_id} executed successfully")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler gracefully.
        
        Args:
            wait: If True, wait for running jobs to complete
        """
        logger.info("Shutting down scheduler...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler was not running")
    
    def get_jobs(self) -> list:
        """
        Get list of scheduled jobs.
        
        Returns:
            List of job information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    def pause(self) -> None:
        """Pause the scheduler."""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume(self) -> None:
        """Resume the scheduler."""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running
