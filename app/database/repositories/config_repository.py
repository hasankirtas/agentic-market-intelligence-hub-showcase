"""
User configuration repository.
"""
from typing import Optional, List, Dict
from google.cloud.firestore import DocumentSnapshot
from app.database.firestore_client import get_firestore_client
from models.config import UserConfig
from datetime import datetime
from core.logger import setup_logger

logger = setup_logger(__name__)


class ConfigRepository:
    """
    Repository for user configuration CRUD operations.
    """
    
    def __init__(self, firestore_client=None):
        """
        Initialize config repository.
        
        Args:
            firestore_client: Firestore Client instance (optional, uses singleton if not provided)
        """
        if firestore_client is not None:
            self.firestore = firestore_client
        else:
            # Fallback to singleton for backward compatibility
            from app.database.firestore_client import FirestoreClient
            self.firestore = FirestoreClient()
        self.collection_name = "users"
    
    async def create_config(self, config: UserConfig) -> UserConfig:
        """
        Create a new user configuration.
        
        Args:
            config: UserConfig model instance
        
        Returns:
            Created UserConfig
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                config.user_id
            )
            
            # Create subcollection for config
            config_ref = doc_ref.collection("config").document("settings")
            
            config_dict = config.model_dump()
            config_dict["created_at"] = config.created_at
            config_dict["updated_at"] = config.updated_at
            
            config_ref.set(config_dict)
            
            logger.info(f"Created config for user: {config.user_id}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create config for user {config.user_id}: {e}")
            raise
    
    async def get_config(self, user_id: str) -> Optional[UserConfig]:
        """
        Get user configuration.
        
        Args:
            user_id: User identifier
        
        Returns:
            UserConfig if found, None otherwise
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                user_id
            )
            config_ref = doc_ref.collection("config").document("settings")
            doc = config_ref.get()
            
            if not doc.exists:
                logger.debug(f"Config not found for user: {user_id}")
                return None
            
            config_dict = doc.to_dict()
            return UserConfig(**config_dict)
            
        except Exception as e:
            logger.error(f"Failed to get config for user {user_id}: {e}")
            return None
    
    async def update_config(self, user_id: str, updates: Dict) -> UserConfig:
        """
        Update user configuration.
        
        Args:
            user_id: User identifier
            updates: Dictionary of fields to update
        
        Returns:
            Updated UserConfig
        
        Raises:
            ValueError: If config not found
        """
        try:
            config = await self.get_config(user_id)
            if not config:
                raise ValueError(f"Config not found for user: {user_id}")
            
            # Update fields
            config_dict = config.model_dump()
            config_dict.update(updates)
            config_dict["updated_at"] = datetime.utcnow()
            
            # Save updated config
            doc_ref = self.firestore.get_document(
                self.collection_name,
                user_id
            )
            config_ref = doc_ref.collection("config").document("settings")
            config_ref.update(config_dict)
            
            logger.info(f"Updated config for user: {user_id}")
            return UserConfig(**config_dict)
            
        except Exception as e:
            logger.error(f"Failed to update config for user {user_id}: {e}")
            raise
    
    async def delete_config(self, user_id: str) -> bool:
        """
        Delete user configuration.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if deleted, False if not found
        """
        try:
            doc_ref = self.firestore.get_document(
                self.collection_name,
                user_id
            )
            config_ref = doc_ref.collection("config").document("settings")
            config_ref.delete()
            
            logger.info(f"Deleted config for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete config for user {user_id}: {e}")
            return False
    
    async def get_all_active_configs(self) -> List[UserConfig]:
        """
        Get all active user configurations.
        
        Returns:
            List of active UserConfig instances
        """
        try:
            configs = []
            users_ref = self.firestore.get_collection(self.collection_name)
            users = users_ref.stream()
            
            for user_doc in users:
                config_ref = user_doc.reference.collection("config").document("settings")
                config_doc = config_ref.get()
                
                if config_doc.exists:
                    config_dict = config_doc.to_dict()
                    if config_dict and config_dict.get("is_active", False):
                        configs.append(UserConfig(**config_dict))
            
            logger.info(f"Retrieved {len(configs)} active configs")
            return configs
            
        except Exception as e:
            logger.error(f"Failed to get all active configs: {e}")
            return []
    
    async def exists(self, user_id: str) -> bool:
        """
        Check if user configuration exists.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if exists, False otherwise
        """
        config = await self.get_config(user_id)
        return config is not None
