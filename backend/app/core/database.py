"""
MongoDB database connection and utilities.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    _connected: bool = False
    
    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
            )
            cls.database = cls.client[settings.MONGODB_DATABASE]
            
            # Verify connection
            await cls.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")
            cls._connected = True
            
            # Create indexes
            await cls._create_indexes()
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            logger.warning("Running without MongoDB - some features will be unavailable")
            # Close the client to stop repeated connection attempts
            if cls.client:
                cls.client.close()
                cls.client = None
            cls.database = None
            cls._connected = False
            # Don't raise - allow app to start for development/testing
    
    @classmethod
    def is_connected(cls) -> bool:
        """Check if MongoDB is connected."""
        return cls._connected
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes for optimal performance."""
        if not cls._connected:
            return
        try:
            # Users collection indexes
            await cls.database.users.create_index("email", unique=True)
            
            # Profiles collection indexes
            await cls.database.profiles.create_index("user_id", unique=True)
            
            # Generated CVs collection indexes
            await cls.database.generated_cvs.create_index("user_id")
            await cls.database.generated_cvs.create_index(
                [("user_id", 1), ("created_at", -1)]
            )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.database
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get a specific collection."""
        return cls.get_database()[collection_name]


# Collection accessors
def get_users_collection():
    """Get users collection."""
    return MongoDB.get_collection("users")


def get_profiles_collection():
    """Get profiles collection."""
    return MongoDB.get_collection("profiles")


def get_generated_cvs_collection():
    """Get generated CVs collection."""
    return MongoDB.get_collection("generated_cvs")


async def get_database():
    """Dependency for getting database instance."""
    return MongoDB.get_database()
