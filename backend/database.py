"""
Unified Database Access Layer supporting MongoDB and SQLite fallback.
When MONGO_URI is reachable, operates natively on MongoDB collections.
"""

import os
import datetime
import sqlite3
from typing import Any, List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from mongo_db import MongoDB, MONGO_URI, DB_NAME

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")


class Database:
    @classmethod
    def is_mongo(cls) -> bool:
        return MongoDB.is_connected()

    @classmethod
    def get_active_engine(cls) -> str:
        return "mongodb" if cls.is_mongo() else "sqlite"

    @classmethod
    def get_mongo_db(cls):
        return MongoDB.get_db()

    # --------------------------------------------------------------------------
    # SQLite Fallback Engine
    # --------------------------------------------------------------------------
    @classmethod
    def get_sqlite_conn(cls):
        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @classmethod
    def query_all(cls, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        conn = cls.get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql.replace("%s", "?"), params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @classmethod
    def query_one(cls, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        conn = cls.get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql.replace("%s", "?"), params)
            r = cursor.fetchone()
            return dict(r) if r else None
        finally:
            conn.close()

    @classmethod
    def execute(cls, sql: str, params: Tuple = ()) -> int:
        conn = cls.get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql.replace("%s", "?"), params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def insert_and_get_id(cls, sql: str, params: Tuple = ()) -> int:
        conn = cls.get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql.replace("%s", "?"), params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def find_one(cls, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if cls.is_mongo():
            return cls.get_mongo_db()[collection_name].find_one(query, {"_id": 0})
        else:
            clauses = [f"{k} = ?" for k in query.keys()]
            sql = f"SELECT * FROM {collection_name} WHERE {' AND '.join(clauses)}"
            return cls.query_one(sql, tuple(query.values()))

    # --------------------------------------------------------------------------
    # Initialization
    # --------------------------------------------------------------------------
    @classmethod
    def init_database(cls):
        """Initializes database schema and collections for both MongoDB and SQLite."""
        if cls.is_mongo():
            MongoDB.init_indexes()
            print("[DATABASE] Using Native MongoDB Engine:", MONGO_URI)
        else:
            conn = cls.get_sqlite_conn()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_name TEXT NOT NULL,
                    department_code TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    register_number TEXT NOT NULL UNIQUE,
                    department_id INTEGER NOT NULL,
                    semester INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS faculty (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    department_id INTEGER NOT NULL,
                    designation TEXT DEFAULT 'Assistant Professor',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT NOT NULL,
                    subject_code TEXT NOT NULL UNIQUE,
                    department_id INTEGER NOT NULL,
                    semester INTEGER NOT NULL,
                    credits INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS faculty_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faculty_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(faculty_id, subject_id),
                    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, subject_id),
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    attendance_date DATE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Not Marked',
                    automata_state TEXT NOT NULL DEFAULT 'S0',
                    marked_by INTEGER NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, subject_id, attendance_date),
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                    FOREIGN KEY (marked_by) REFERENCES users(id) ON DELETE SET NULL
                );
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attendance_id INTEGER NOT NULL,
                    previous_state TEXT NOT NULL,
                    input_symbol TEXT NOT NULL,
                    next_state TEXT NOT NULL,
                    changed_by INTEGER NULL,
                    reason TEXT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (attendance_id) REFERENCES attendance(id) ON DELETE CASCADE,
                    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
                );
                """)
                conn.commit()
                print("[DATABASE] Using SQLite Offline Engine (attendance.db)")
            finally:
                conn.close()

    # --------------------------------------------------------------------------
    # High-Level Native MongoDB Repository Methods
    # --------------------------------------------------------------------------
    @classmethod
    def mongo_get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        db = cls.get_mongo_db()
        return db.users.find_one({"email": email.strip().lower()}, {"_id": 0})

    @classmethod
    def mongo_get_user_by_id(cls, user_id: int) -> Optional[Dict[str, Any]]:
        db = cls.get_mongo_db()
        return db.users.find_one({"id": int(user_id)}, {"_id": 0})

    @classmethod
    def mongo_get_demo_users(cls) -> List[Dict[str, Any]]:
        db = cls.get_mongo_db()
        target_emails = [
            'admin@college.edu',
            'faculty1@college.edu',
            'faculty2@college.edu',
            'student1@college.edu',
            'student8@college.edu'
        ]
        users = list(db.users.find({"email": {"$in": target_emails}}, {"_id": 0}))
        for u in users:
            dept_code = ""
            if u["role"] == "faculty":
                f = db.faculty.find_one({"user_id": u["id"]})
                if f:
                    d = db.departments.find_one({"id": f["department_id"]})
                    if d: dept_code = d.get("department_code", "")
            elif u["role"] == "student":
                s = db.students.find_one({"user_id": u["id"]})
                if s:
                    d = db.departments.find_one({"id": s["department_id"]})
                    if d: dept_code = d.get("department_code", "")
            u["dept_code"] = dept_code
        return users
