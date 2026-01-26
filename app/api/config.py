"""
Configuration endpoints.
CRUD operations for user configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.dependencies import get_config_repository
from app.database.repositories.config_repository import ConfigRepository
from app.api.schemas import (
    ConfigCreateRequest,
    ConfigUpdateRequest,
    ConfigResponse,
    ErrorResponse
)
from models.config import UserConfig
from datetime import datetime

router = APIRouter(prefix="/api/config", tags=["config"])


@router.post("/", response_model=ConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    request: ConfigCreateRequest,
    repository: ConfigRepository = Depends(get_config_repository)
) -> ConfigResponse:
    """
    Create a new user configuration.
    
    Args:
        request: Configuration creation request
        repository: ConfigRepository dependency
    
    Returns:
        Created configuration
    
    Raises:
        HTTPException: If configuration already exists or creation fails
    """
    try:
        # Check if config already exists
        if await repository.exists(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Configuration already exists for user: {request.user_id}"
            )
        
        # Create UserConfig model
        config = UserConfig(
            user_id=request.user_id,
            urls=request.urls,
            scan_schedule=request.scan_schedule,
            report_schedule=request.report_schedule,
            emergency_email_enabled=request.emergency_email_enabled,
            email=request.email,
            thresholds=request.thresholds,
            is_active=request.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        created_config = await repository.create_config(config)
        
        return ConfigResponse.from_user_config(created_config)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create configuration: {str(e)}"
        )


@router.get("/{user_id}", response_model=ConfigResponse)
async def get_config(
    user_id: str,
    repository: ConfigRepository = Depends(get_config_repository)
) -> ConfigResponse:
    """
    Get user configuration.
    
    Args:
        user_id: User identifier
        repository: ConfigRepository dependency
    
    Returns:
        User configuration
    
    Raises:
        HTTPException: If configuration not found
    """
    try:
        config = await repository.get_config(user_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found for user: {user_id}"
            )
        
        return ConfigResponse.from_user_config(config)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.put("/{user_id}", response_model=ConfigResponse)
async def update_config(
    user_id: str,
    request: ConfigUpdateRequest,
    repository: ConfigRepository = Depends(get_config_repository)
) -> ConfigResponse:
    """
    Update user configuration.
    
    Args:
        user_id: User identifier
        request: Configuration update request (only provided fields will be updated)
        repository: ConfigRepository dependency
    
    Returns:
        Updated configuration
    
    Raises:
        HTTPException: If configuration not found or update fails
    """
    try:
        # Build update dict (only include non-None fields)
        updates = {}
        if request.urls is not None:
            updates["urls"] = request.urls
        if request.scan_schedule is not None:
            updates["scan_schedule"] = request.scan_schedule
        if request.report_schedule is not None:
            updates["report_schedule"] = request.report_schedule
        if request.emergency_email_enabled is not None:
            updates["emergency_email_enabled"] = request.emergency_email_enabled
        if request.email is not None:
            updates["email"] = request.email
        if request.thresholds is not None:
            updates["thresholds"] = request.thresholds
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        
        if not updates:
            # No updates provided, return current config
            config = await repository.get_config(user_id)
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Configuration not found for user: {user_id}"
                )
            return ConfigResponse.from_user_config(config)
        
        # Update configuration
        updated_config = await repository.update_config(user_id, updates)
        
        return ConfigResponse.from_user_config(updated_config)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    user_id: str,
    repository: ConfigRepository = Depends(get_config_repository)
):
    """
    Delete user configuration.
    
    Args:
        user_id: User identifier
        repository: ConfigRepository dependency
    
    Raises:
        HTTPException: If deletion fails
    """
    try:
        deleted = await repository.delete_config(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration not found for user: {user_id}"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )


@router.get("/", response_model=List[ConfigResponse])
async def list_active_configs(
    repository: ConfigRepository = Depends(get_config_repository)
) -> List[ConfigResponse]:
    """
    List all active user configurations.
    
    Args:
        repository: ConfigRepository dependency
    
    Returns:
        List of active configurations
    """
    try:
        configs = await repository.get_all_active_configs()
        return [ConfigResponse.from_user_config(config) for config in configs]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list configurations: {str(e)}"
        )
