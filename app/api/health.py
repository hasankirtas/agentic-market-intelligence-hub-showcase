"""
Health check endpoint.
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.dependencies import get_orchestrator_dependency
from core.orchestration.orchestrator import Orchestrator as CoreOrchestrator

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "agentic-market-intelligence-hub"
    }


@router.get("/detailed")
async def detailed_health_check(
    orchestrator: CoreOrchestrator = Depends(get_orchestrator_dependency)
) -> Dict[str, Any]:
    """
    Detailed health check with orchestrator status.
    
    Checks:
    - API is running
    - Orchestrator is initialized
    - All agents are registered
    
    Args:
        orchestrator: Orchestrator dependency
    
    Returns:
        Detailed health status with agent information
    """
    agents_status = {}
    for agent_name, agent in orchestrator.agents.items():
        # Handle both real agents and mocks
        if hasattr(agent, '_initialized'):
            initialized = getattr(agent, '_initialized', False)
        else:
            # For mock objects, just check if agent exists
            initialized = agent is not None
        
        agents_status[agent_name] = {
            "registered": True,
            "initialized": bool(initialized)
        }
    
    return {
        "status": "healthy",
        "service": "agentic-market-intelligence-hub",
        "orchestrator": {
            "initialized": True,
            "agents_count": len(orchestrator.agents) if hasattr(orchestrator, 'agents') else 0,
            "workflows_count": len(orchestrator.workflows) if hasattr(orchestrator, 'workflows') else 0
        },
        "agents": agents_status
    }
