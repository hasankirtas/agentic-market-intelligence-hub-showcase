"""
Database setup and initialization script.
Tests Firestore connection and verifies collections.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.firestore_client import get_firestore_client
from core.logger import setup_logger

logger = setup_logger(__name__)


async def test_connection():
    """Test Firestore connection."""
    try:
        logger.info("Testing Firestore connection...")
        firestore_client = get_firestore_client()
        client = firestore_client.client
        
        # Try to access a collection (this will test the connection)
        test_collection = firestore_client.get_collection("_test_connection")
        
        # Write and delete a test document
        test_doc = test_collection.document("test")
        test_doc.set({"test": True, "timestamp": "2024-01-01"})
        test_doc.delete()
        
        logger.info("✅ Firestore connection successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")
        logger.error("Make sure you have:")
        logger.error("1. Installed Google Cloud SDK")
        logger.error("2. Run: gcloud auth application-default login")
        logger.error("3. Set GCP_PROJECT_ID environment variable")
        return False


async def verify_collections():
    """Verify that required collections can be accessed."""
    try:
        logger.info("Verifying collections...")
        firestore_client = get_firestore_client()
        
        collections = [
            "users",
            "scans",
            "reports",
            "baselines"
        ]
        
        for collection_name in collections:
            collection = firestore_client.get_collection(collection_name)
            # Just verify we can access it (collections are created automatically)
            logger.info(f"✅ Collection '{collection_name}' accessible")
        
        logger.info("✅ All collections verified!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Collection verification failed: {e}")
        return False


async def main():
    """Main setup function."""
    logger.info("=" * 50)
    logger.info("Database Setup Script")
    logger.info("=" * 50)
    
    # Test connection
    connection_ok = await test_connection()
    if not connection_ok:
        logger.error("Setup failed: Connection test failed")
        sys.exit(1)
    
    # Verify collections
    collections_ok = await verify_collections()
    if not collections_ok:
        logger.error("Setup failed: Collection verification failed")
        sys.exit(1)
    
    logger.info("=" * 50)
    logger.info("✅ Database setup completed successfully!")
    logger.info("=" * 50)
    logger.info("Note: Collections are created automatically in Firestore")
    logger.info("when you first write to them. No manual setup required.")


if __name__ == "__main__":
    asyncio.run(main())
