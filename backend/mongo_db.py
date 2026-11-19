"""
Native MongoDB Database Engine for Automated Attendance Management System
Supports Local MongoDB (mongodb://localhost:27017) and MongoDB Atlas (mongodb+srv://...)
"""

import os
import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load .env variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

MONGO_URI = os.environ.get(
    "MONGO_URI",
    os.environ.get("MONGODB_URI", "mongodb://localhost:27017/attendance_system")
)

DB_NAME = "attendance_system"


class MongoDB:
    _client: Optional[MongoClient] = None
    _db = None
    _connected = False

    @classmethod
    def get_client(cls) -> Optional[MongoClient]:
        if cls._client is None:
            try:
                cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
                # Verify connection with ping
                cls._client.admin.command("ping")
                cls._connected = True
                print(f"[MONGODB] Connected successfully to: {MONGO_URI.split('@')[-1]}")
            except Exception as e:
                cls._connected = False
                print(f"[MONGODB WARNING] Could not connect to MongoDB at {MONGO_URI}: {e}")
                print("[MONGODB INFO] To use MongoDB, ensure mongod is running or update MONGO_URI in .env.")
                cls._client = None
                return None
        return cls._client

    @classmethod
    def get_db(cls):
        client = cls.get_client()
        if client:
            return client.get_database(DB_NAME)
        return None

    @classmethod
    def is_connected(cls) -> bool:
        if cls._client is None:
            cls.get_client()
        return cls._connected

    @classmethod
    def init_indexes(cls):
        """Creates unique indexes for data integrity in MongoDB collections."""
        db = cls.get_db()
        if db is None:
            return

        db.users.create_index([("email", ASCENDING)], unique=True)
        db.departments.create_index([("department_code", ASCENDING)], unique=True)
        db.students.create_index([("register_number", ASCENDING)], unique=True)
        db.students.create_index([("user_id", ASCENDING)], unique=True)
        db.faculty.create_index([("user_id", ASCENDING)], unique=True)
        db.subjects.create_index([("subject_code", ASCENDING)], unique=True)
        db.faculty_subjects.create_index([("faculty_id", ASCENDING), ("subject_id", ASCENDING)], unique=True)
        db.enrollments.create_index([("student_id", ASCENDING), ("subject_id", ASCENDING)], unique=True)
        db.attendance.create_index(
            [("student_id", ASCENDING), ("subject_id", ASCENDING), ("attendance_date", ASCENDING)],
            unique=True
        )
        db.attendance_logs.create_index([("attendance_id", ASCENDING)])
        db.attendance_logs.create_index([("timestamp", DESCENDING)])
        print("[MONGODB] Indexes verified for all collections.")

    @classmethod
    def get_next_id(cls, collection_name: str) -> int:
        """Sequential integer IDs for easy human readability and backwards compatibility."""
        db = cls.get_db()
        if db is None:
            return 1
        counter = db.counters.find_one_and_update(
            {"_id": collection_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return counter["seq"]
