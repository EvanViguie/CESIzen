from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import os
from typing import Optional

# MongoDB connection parameters — use environment variables in production
MONGO_HOST = os.environ.get("MONGO_HOST", "mongo")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_URI = os.environ.get("MONGO_URI", f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
DB_NAME = os.environ.get("MONGO_DB_NAME", "cesizen_auth")

# Singleton pattern for MongoDB connection
class MongoDB:
    _instance: Optional["MongoDB"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._client = MongoClient(MONGO_URI)
            cls._db = cls._client[DB_NAME]
        return cls._instance

    @property
    def client(self) -> MongoClient:
        return self._client

    @property
    def db(self) -> Database:
        return self._db

    def get_collection(self, collection_name: str) -> Collection:
        return self._db[collection_name]

    def close(self):
        if self._client:
            self._client.close()
            MongoDB._client = None
            MongoDB._db = None
            MongoDB._instance = None

# Create a MongoDB connection instance
mongo_db = MongoDB()

# Get collections
users_collection = mongo_db.get_collection("users")