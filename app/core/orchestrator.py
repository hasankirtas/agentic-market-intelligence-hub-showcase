"""
Singleton orchestrator instance.
Manages agent registration and workflow execution.
"""
from typing import Optional, Dict, Any
from core.orchestration.orchestrator import Orchestrator as CoreOrchestrator
from agents.watcher_agent import WatcherAgent
from agents.analyst_agent import AnalystAgent
from agents.reporter_agent import ReporterAgent
from app.core.config import get_settings
from core.logger import setup_logger

logger = setup_logger(__name__)

# Global orchestrator instance
_orchestrator: Optional[CoreOrchestrator] = None


def get_orchestrator() -> CoreOrchestrator:
    """
    Get or create singleton orchestrator instance.
    
    Initializes orchestrator with all agents registered.
    Agents are configured from application settings.
    
    Returns:
        CoreOrchestrator instance with all agents registered
    
    Raises:
        Exception: If agent initialization fails
    """
    global _orchestrator
    
    if _orchestrator is None:
        settings = get_settings()
        
        logger.info("Initializing orchestrator...")
        _orchestrator = CoreOrchestrator()
        
        # Initialize and register Watcher Agent
        watcher_config = {
            "crawler_config": {
                "timeout": settings.crawler_timeout,
                "use_playwright": settings.crawler_use_playwright,
                "wait_for": settings.crawler_wait_for
            },
            "parser_config": {}
        }
        logger.info(f"Watcher config - use_playwright: {settings.crawler_use_playwright} (type: {type(settings.crawler_use_playwright)})")  # DEBUG
        watcher = WatcherAgent(
            agent_id=settings.watcher_agent_id,
            config=watcher_config
        )
        _orchestrator.register_agent(settings.watcher_agent_id, watcher)
        logger.info(f"Registered agent: {settings.watcher_agent_id}")
        
        # Initialize and register Analyst Agent
        analyst_config = {
            "critical_threshold": settings.critical_threshold,
            "price_change_threshold": settings.price_change_threshold
        }
        analyst = AnalystAgent(
            agent_id=settings.analyst_agent_id,
            config=analyst_config
        )
        _orchestrator.register_agent(settings.analyst_agent_id, analyst)
        logger.info(f"Registered agent: {settings.analyst_agent_id}")
        
        # Initialize and register Reporter Agent
        reporter_config = {
            "llm_config": {
                "api_key": settings.openai_api_key,
                "model": settings.openai_model,
                "temperature": settings.openai_temperature,
                "max_tokens": settings.openai_max_tokens
            },
            "generate_html": settings.reporter_generate_html,
            "max_change_records": settings.reporter_max_change_records
        }
        reporter = ReporterAgent(
            agent_id=settings.reporter_agent_id,
            config=reporter_config
        )
        _orchestrator.register_agent(settings.reporter_agent_id, reporter)
        logger.info(f"Registered agent: {settings.reporter_agent_id}")
        
        # Initialize all agents
        logger.info("Initializing agents...")
        # Note: Agents will be initialized on first use via their process() methods
        # or we can initialize them here if needed
        
        logger.info("Orchestrator initialization complete")
    
    return _orchestrator


async def initialize_orchestrator() -> None:
    """
    Initialize orchestrator and all agents.
    
    Call this during FastAPI startup to ensure agents are ready.
    """
    orchestrator = get_orchestrator()
    
    # Initialize all registered agents
    for agent_name, agent in orchestrator.agents.items():
        try:
            await agent.initialize()
            logger.info(f"Initialized agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_name}: {e}")
            raise


async def cleanup_orchestrator() -> None:
    """
    Cleanup orchestrator and all agents.
    
    Call this during FastAPI shutdown to release resources.
    """
    global _orchestrator
    
    if _orchestrator is not None:
        # Cleanup all registered agents
        for agent_name, agent in _orchestrator.agents.items():
            try:
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
                logger.info(f"Cleaned up agent: {agent_name}")
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_name}: {e}")
        
        _orchestrator = None
        logger.info("Orchestrator cleaned up")
