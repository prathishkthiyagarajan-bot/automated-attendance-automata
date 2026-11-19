"""
Unified Database Access Layer
Supports SQLite (zero-config, out-of-the-box local operation) and MySQL (production database).
"""

import os
import sqlite3
import pymysql
from contextlib import contextmanager
from typing import Any, List, Dict, Optional, Tuple

DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()
DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "attendance.db")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "attendance_system")


def get_active_db_type() -> str:
    """Detect if MySQL is explicitly configured and connectable, otherwise fallback to SQLite."""
    global DB_TYPE
    if DB_TYPE == "mysql":
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                connect_timeout=2
            )
            conn.close()
            return "mysql"
        except Exception:
            # Fallback to sqlite if MySQL connection fails
            return "sqlite"
    return "sqlite"


class Database:
    @staticmethod
    def get_connection():
        driver = get_active_db_type()
        if driver == "mysql":
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            return conn, "mysql"
        else:
            conn = sqlite3.connect(DB_FILE, timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn, "sqlite"

    @classmethod
    def format_query(cls, sql: str, driver: str) -> str:
        """Translate SQL syntax between MySQL and SQLite where necessary."""
        if driver == "sqlite":
            # Translate MySQL placeholders (%s) to SQLite (?)
            sql = sql.replace("%s", "?")
        return sql

    @classmethod
    def query_all(cls, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        conn, driver = cls.get_connection()
        try:
            cursor = conn.cursor()
            formatted_sql = cls.format_query(sql, driver)
            cursor.execute(formatted_sql, params)
            if driver == "mysql":
                rows = cursor.fetchall()
            else:
                rows = [dict(row) for row in cursor.fetchall()]
            return rows
        finally:
            conn.close()

    @classmethod
    def query_one(cls, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        conn, driver = cls.get_connection()
        try:
            cursor = conn.cursor()
            formatted_sql = cls.format_query(sql, driver)
            cursor.execute(formatted_sql, params)
            if driver == "mysql":
                row = cursor.fetchone()
            else:
                r = cursor.fetchone()
                row = dict(r) if r else None
            return row
        finally:
            conn.close()

    @classmethod
    def execute(cls, sql: str, params: Tuple = ()) -> int:
        conn, driver = cls.get_connection()
        try:
            cursor = conn.cursor()
            formatted_sql = cls.format_query(sql, driver)
            cursor.execute(formatted_sql, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def insert_and_get_id(cls, sql: str, params: Tuple = ()) -> int:
        conn, driver = cls.get_connection()
        try:
            cursor = conn.cursor()
            formatted_sql = cls.format_query(sql, driver)
            cursor.execute(formatted_sql, params)
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @classmethod
    def init_database(cls):
        """Initializes tables for SQLite if not already created."""
        conn, driver = cls.get_connection()
        try:
            cursor = conn.cursor()
            if driver == "sqlite":
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
            print(f"[DATABASE] Initialized tables successfully with driver: {driver}")
        finally:
            conn.close()
