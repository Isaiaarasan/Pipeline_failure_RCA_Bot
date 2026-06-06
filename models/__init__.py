import logging
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

# Global database reference
db = None
is_mock = False

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.documents = []
        self._next_id = 1

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = self._next_id
            self._next_id += 1
        self.documents.append(document)
        class InsertResult:
            inserted_id = document["_id"]
        return InsertResult()

    def find_one(self, query):
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, query=None, sort=None):
        query = query or {}
        results = []
        for doc in self.documents:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)
                
        if sort:
            # Simple sorting simulation for uploaded_at or created_at
            key = sort[0][0]
            reverse = (sort[0][1] == -1)
            results.sort(key=lambda x: x.get(key) if x.get(key) is not None else "", reverse=reverse)
            
        return results

    def count_documents(self, query=None):
        query = query or {}
        return len(self.find(query))

    def find_one_and_update(self, filter_query, update_query, upsert=False, return_document=None):
        doc = self.find_one(filter_query)
        if not doc:
            if upsert:
                # Basic upsert logic
                doc = filter_query.copy()
                if "$inc" in update_query:
                    for k, v in update_query["$inc"].items():
                        doc[k] = v
                self.documents.append(doc)
                return doc
            return None
            
        # Basic update logic
        if "$inc" in update_query:
            for k, v in update_query["$inc"].items():
                doc[k] = doc.get(k, 0) + v
        if "$set" in update_query:
            for k, v in update_query["$set"].items():
                doc[k] = v
        return doc

class MockMongoDB:
    def __init__(self):
        self.collections = {}
        logger.warning("Initializing Mock In-Memory Database client.")

    def __getattr__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    def get_collection(self, name):
        return self.__getattr__(name)

def init_db(uri):
    global db, is_mock
    try:
        logger.info(f"Connecting to MongoDB at: {uri}")
        # Use a small server selection timeout to avoid long blocking when MongoDB is unreachable
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=500)
        # Ping check
        client.admin.command('ping')
        db = client.get_database()  # Extracts default db from URI or uses 'rca_bot'
        is_mock = False
        logger.info("Successfully connected to live MongoDB server.")
    except Exception as e:
        # Catch any exception to ensure we gracefully fallback to the in-memory mock
        logger.warning(f"Could not connect to live MongoDB server ({str(e)}). Falling back to In-Memory simulation.")
        db = MockMongoDB()
        is_mock = True
    return db
