import logging
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global database reference
db = None

def init_db(uri):
    global db
    logger.info(f"Connecting to MongoDB at: {uri}")
    # Use a small server selection timeout to avoid long blocking when MongoDB is unreachable
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=500)
    # Ping check
    client.admin.command('ping')
    db = client.get_database()  # Extracts default db from URI or uses 'rca_bot'
    logger.info("Successfully connected to live MongoDB server.")
    return db
