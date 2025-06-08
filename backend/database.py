from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from config import settings
import structlog
from typing import Optional

logger = structlog.get_logger()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

database = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        database.client = AsyncIOMotorClient(settings.mongo_url)
        database.db = database.client[settings.db_name]
        
        # Test the connection
        await database.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        # Users collection indexes
        users_indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("last_login", DESCENDING)]),
        ]
        await database.db.users.create_indexes(users_indexes)
        
        # Chats collection indexes
        chats_indexes = [
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("pinned", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("title", TEXT)]),
        ]
        await database.db.chats.create_indexes(chats_indexes)
        
        # Messages collection indexes
        messages_indexes = [
            IndexModel([("chat_id", ASCENDING), ("created_at", ASCENDING)]),
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("content", TEXT)]),
        ]
        await database.db.messages.create_indexes(messages_indexes)
        
        # Sessions collection indexes
        sessions_indexes = [
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("token", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]
        await database.db.sessions.create_indexes(sessions_indexes)
        
        # Rate limiting collection indexes
        rate_limits_indexes = [
            IndexModel([("key", ASCENDING), ("window", ASCENDING)]),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]
        await database.db.rate_limits.create_indexes(rate_limits_indexes)
        
        # Files collection indexes
        files_indexes = [
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("chat_id", ASCENDING)]),
            IndexModel([("file_hash", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
        await database.db.files.create_indexes(files_indexes)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database.db is None:
        raise Exception("Database not initialized")
    return database.db