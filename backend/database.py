"""MongoDB access and one-time migration from the legacy SQLite database."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, ReturnDocument

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/attendance_system")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "attendance_system")
SQLITE_FILE = Path(__file__).resolve().parent.parent / "attendance.db"

COLLECTIONS = (
    "users",
    "departments",
    "students",
    "faculty",
    "subjects",
    "faculty_subjects",
    "enrollments",
    "attendance",
    "attendance_logs",
)


class Database:
    client = None
    database = None

    @classmethod
    def init_database(cls):
        if cls.client is None:
            cls.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            cls.database = cls.client[MONGODB_DATABASE]

        cls.client.admin.command("ping")
        cls._ensure_indexes()
        cls._migrate_sqlite()
        print(f"[DATABASE] Connected to MongoDB database: {MONGODB_DATABASE}")

    @classmethod
    def _ensure_indexes(cls):
        indexes = {
            "users": [("email",)],
            "departments": [("department_code",)],
            "students": [("user_id",), ("register_number",)],
            "faculty": [("user_id",)],
            "subjects": [("subject_code",)],
        }
        for collection, fields in indexes.items():
            for field in fields:
                cls.collection(collection).create_index(field[0], unique=True)

        cls.collection("faculty_subjects").create_index(
            [("faculty_id", 1), ("subject_id", 1)], unique=True
        )
        cls.collection("enrollments").create_index(
            [("student_id", 1), ("subject_id", 1)], unique=True
        )
        cls.collection("attendance").create_index(
            [("student_id", 1), ("subject_id", 1), ("attendance_date", 1)],
            unique=True,
        )
        cls.collection("attendance_logs").create_index("attendance_id")

    @classmethod
    def _migrate_sqlite(cls):
        if not SQLITE_FILE.exists():
            return

        system = cls.collection("_system")
        marker_id = "sqlite_migration_v1"
        marker = system.find_one({"_id": marker_id})
        if marker and marker.get("status") == "completed":
            return

        if marker is None:
            existing_data = any(cls.collection(name).count_documents({}) for name in COLLECTIONS)
            if existing_data:
                raise RuntimeError(
                    "MongoDB already contains application data but has no SQLite migration "
                    "marker. Refusing to combine databases."
                )
            system.insert_one({"_id": marker_id, "status": "in_progress"})

        with sqlite3.connect(str(SQLITE_FILE)) as source:
            source.row_factory = sqlite3.Row
            tables = {
                row["name"]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            for name in COLLECTIONS:
                if name not in tables:
                    continue
                rows = source.execute(f'SELECT * FROM "{name}"').fetchall()
                target = cls.collection(name)
                for row in rows:
                    document = dict(row)
                    document["id"] = int(document["id"])
                    document["_id"] = document["id"]
                    target.replace_one({"_id": document["_id"]}, document, upsert=True)
                if rows:
                    cls.collection("_counters").replace_one(
                        {"_id": name},
                        {"_id": name, "sequence": max(int(row["id"]) for row in rows)},
                        upsert=True,
                    )

        system.update_one({"_id": marker_id}, {"$set": {"status": "completed"}})
        print(f"[DATABASE] Migrated legacy SQLite data from {SQLITE_FILE}")

    @classmethod
    def collection(cls, name):
        if cls.database is None:
            cls.init_database()
        return cls.database[name]

    @classmethod
    def find(cls, name, query=None, sort=None, limit=None):
        cursor = cls.collection(name).find(query or {}, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    @classmethod
    def find_one(cls, name, query):
        return cls.collection(name).find_one(query, {"_id": 0})

    @classmethod
    def count(cls, name, query=None):
        return cls.collection(name).count_documents(query or {})

    @classmethod
    def insert(cls, name, document):
        record = dict(document)
        if "id" not in record:
            counter = cls.collection("_counters").find_one_and_update(
                {"_id": name},
                {"$inc": {"sequence": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            record["id"] = counter["sequence"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if name in {"users", "departments", "students", "faculty", "subjects"}:
            record.setdefault("created_at", now)
        elif name == "faculty_subjects":
            record.setdefault("assigned_at", now)
        elif name == "enrollments":
            record.setdefault("enrolled_at", now)
        elif name == "attendance":
            record.setdefault("created_at", now)
            record.setdefault("updated_at", now)
        elif name == "attendance_logs":
            record.setdefault("timestamp", now)

        record["_id"] = record["id"]
        cls.collection(name).insert_one(record)
        return record["id"]

    @classmethod
    def update(cls, name, query, values, upsert=False):
        return cls.collection(name).update_one(
            query, {"$set": values}, upsert=upsert
        )

    @classmethod
    def delete(cls, name, query):
        return cls.collection(name).delete_many(query).deleted_count
