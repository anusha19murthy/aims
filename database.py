"""MongoDB connection helpers. Set MONGODB_URI in the deployment environment."""
import os
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database

_client: MongoClient | None = None

def get_database() -> Database:
    global _client
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured")
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client.get_default_database(default="cogniscribe")

def ensure_indexes() -> None:
    db = get_database()
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.patients.create_index([("doctor_id", ASCENDING), ("appointment_date", ASCENDING)])
    db.notes.create_index([("patient_id", ASCENDING), ("created_at", ASCENDING)])
