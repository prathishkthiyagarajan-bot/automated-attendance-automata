"""
Automated Attendance Management System Using Finite Automata
Flask RESTful Backend Application & Static Asset Server
Dual Database Support: MongoDB (Native) and SQLite (Offline Fallback)
"""

import os
import sys
import datetime
import io
import csv
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Load .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(__file__))

from mongo_db import MongoDB, MONGO_URI
from database import Database
from dfa_engine import AttendanceDFA, DFAState, DFAAlphabet

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
    static_url_path=""
)
CORS(app)

# Initialize Database and seed on startup if needed
Database.init_database()
from seed_data import seed_all
seed_all()

# ==============================================================================
# Helper functions
# ==============================================================================

def get_current_user_from_header():
    user_id = request.headers.get("X-User-Id") or request.args.get("user_id")
    if not user_id:
        return None

    if Database.is_mongo():
        db = Database.get_mongo_db()
        return db.users.find_one({"id": int(user_id)}, {"_id": 0, "password": 0})
    else:
        return Database.query_one("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))

def status_from_state(state: str) -> str:
    mapping = {
        DFAState.S0: "Not Marked",
        DFAState.S1: "Present",
        DFAState.S2: "Absent",
        DFAState.S3: "Late",
        DFAState.S4: "Finalized"
    }
    return mapping.get(state, "Not Marked")

# ==============================================================================
# Status & Database Engine Info
# ==============================================================================

@app.route("/api/system/info", methods=["GET"])
def system_info():
    """Returns runtime database engine (MongoDB or SQLite)."""
    is_mongo = Database.is_mongo()
    return jsonify({
        "success": True,
        "database_engine": "MongoDB" if is_mongo else "SQLite",
        "mongo_connected": is_mongo,
        "mongo_uri": MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI,
        "status": "Online",
        "automata_engine": "Deterministic Finite Automaton (DFA) M=(Q, Σ, δ, q0, F)"
    })

# ==============================================================================
# Authentication & Demo Accounts
# ==============================================================================

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    if Database.is_mongo():
        db = Database.get_mongo_db()
        user = db.users.find_one({"email": email})
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"success": False, "error": "Invalid email or password."}), 401

        role = user["role"]
        extra_info = {}

        if role == "faculty":
            fac = db.faculty.find_one({"user_id": user["id"]})
            if fac:
                dept = db.departments.find_one({"id": fac["department_id"]}) or {}
                extra_info = {
                    "faculty_id": fac["id"],
                    "department_id": fac["department_id"],
                    "department_name": dept.get("department_name", ""),
                    "department_code": dept.get("department_code", ""),
                    "designation": fac.get("designation", "")
                }
        elif role == "student":
            stud = db.students.find_one({"user_id": user["id"]})
            if stud:
                dept = db.departments.find_one({"id": stud["department_id"]}) or {}
                extra_info = {
                    "student_id": stud["id"],
                    "register_number": stud.get("register_number", ""),
                    "department_id": stud["department_id"],
                    "department_name": dept.get("department_name", ""),
                    "department_code": dept.get("department_code", ""),
                    "semester": stud.get("semester", 1)
                }

        return jsonify({
            "success": True,
            "token": f"token-{user['id']}-{role}",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": role,
                **extra_info
            }
        })

    else:
        # SQLite Engine
        user = Database.query_one("SELECT * FROM users WHERE LOWER(email) = %s", (email,))
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"success": False, "error": "Invalid email or password."}), 401

        role = user["role"]
        extra_info = {}

        if role == "faculty":
            fac = Database.query_one("""
                SELECT f.id as faculty_id, f.department_id, d.department_name, d.department_code, f.designation
                FROM faculty f
                JOIN departments d ON f.department_id = d.id
                WHERE f.user_id = %s
            """, (user["id"],))
            if fac: extra_info = fac
        elif role == "student":
            stud = Database.query_one("""
                SELECT s.id as student_id, s.register_number, s.department_id, d.department_name, d.department_code, s.semester
                FROM students s
                JOIN departments d ON s.department_id = d.id
                WHERE s.user_id = %s
            """, (user["id"],))
            if stud: extra_info = stud

        return jsonify({
            "success": True,
            "token": f"token-{user['id']}-{role}",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": role,
                **extra_info
            }
        })

@app.route("/api/auth/demo-users", methods=["GET"])
def get_demo_users():
    if Database.is_mongo():
        return jsonify({"success": True, "demo_users": Database.mongo_get_demo_users()})

    users = Database.query_all("""
        SELECT u.id, u.name, u.email, u.role,
               COALESCE(d.department_code, '') as dept_code
        FROM users u
        LEFT JOIN faculty f ON u.id = f.user_id
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN departments d ON (f.department_id = d.id OR s.department_id = d.id)
        WHERE u.email IN (
            'admin@college.edu',
            'faculty1@college.edu',
            'faculty2@college.edu',
            'student1@college.edu',
            'student8@college.edu'
        )
        ORDER BY u.role, u.id
    """)
    return jsonify({"success": True, "demo_users": users})

# ==============================================================================
# Finite Automata (DFA) Endpoints
# ==============================================================================

@app.route("/api/dfa/info", methods=["GET"])
def get_dfa_info():
    return jsonify({
        "success": True,
        "dfa": AttendanceDFA.get_formal_definition()
    })

@app.route("/api/dfa/simulate", methods=["POST"])
def simulate_dfa():
    data = request.get_json() or {}
    initial_state = data.get("initial_state", DFAState.S0)
    sequence = data.get("sequence", [])
    role = data.get("role", "faculty")

    result = AttendanceDFA.simulate_sequence(initial_state, sequence, role=role)
    return jsonify({"success": True, "simulation": result})

# ==============================================================================
# Attendance Worksheet & DFA Transitions
# ==============================================================================

@app.route("/api/attendance/sheet", methods=["GET"])
def get_attendance_sheet():
    subject_id = request.args.get("subject_id")
    date_str = request.args.get("date")

    if not subject_id or not date_str:
        return jsonify({"success": False, "error": "subject_id and date are required."}), 400

    s_id = int(subject_id)

    if Database.is_mongo():
        db = Database.get_mongo_db()
        subject = db.subjects.find_one({"id": s_id}, {"_id": 0})
        if not subject:
            return jsonify({"success": False, "error": "Subject not found."}), 404

        enrollments = list(db.enrollments.find({"subject_id": s_id}))
        students = []
        is_session_finalized = False

        for e in enrollments:
            st = db.students.find_one({"id": e["student_id"]})
            if not st: continue
            u = db.users.find_one({"id": st["user_id"]}) or {}

            att = db.attendance.find_one({
                "student_id": st["id"],
                "subject_id": s_id,
                "attendance_date": date_str
            })

            curr_state = att["automata_state"] if att else DFAState.S0
            curr_status = att["status"] if att else "Not Marked"
            att_id = att["id"] if att else None

            if curr_state == DFAState.S4:
                is_session_finalized = True

            # Calculate allowed DFA transitions
            valid_actions = []
            for symbol, name in DFAAlphabet.DESCRIPTIONS.items():
                check = AttendanceDFA.validate_transition(curr_state, symbol, user_role="faculty")
                if check.valid:
                    valid_actions.append({
                        "symbol": symbol,
                        "name": name,
                        "target_state": check.next_state,
                        "target_state_name": DFAState.NAMES.get(check.next_state, "")
                    })

            students.append({
                "student_id": st["id"],
                "register_number": st.get("register_number", ""),
                "semester": st.get("semester", 1),
                "name": u.get("name", "Student"),
                "email": u.get("email", ""),
                "attendance_id": att_id,
                "automata_state": curr_state,
                "status": curr_status,
                "allowed_transitions": valid_actions
            })

        students.sort(key=lambda x: x["register_number"])

        return jsonify({
            "success": True,
            "subject": subject,
            "date": date_str,
            "is_finalized": is_session_finalized,
            "students": students,
            "total_enrolled": len(students)
        })

    else:
        # SQLite
        subject = Database.query_one("SELECT * FROM subjects WHERE id = %s", (subject_id,))
        if not subject:
            return jsonify({"success": False, "error": "Subject not found."}), 404

        students = Database.query_all("""
            SELECT s.id as student_id, s.register_number, s.semester, u.name, u.email,
                   a.id as attendance_id,
                   COALESCE(a.automata_state, 'S0') as automata_state,
                   COALESCE(a.status, 'Not Marked') as status,
                   a.marked_by,
                   a.updated_at
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = %s AND a.attendance_date = %s
            WHERE e.subject_id = %s
            ORDER BY s.register_number ASC
        """, (subject_id, date_str, subject_id))

        is_session_finalized = any(s["automata_state"] == DFAState.S4 for s in students) if students else False

        for s in students:
            curr_state = s["automata_state"]
            valid_actions = []
            for symbol, name in DFAAlphabet.DESCRIPTIONS.items():
                check = AttendanceDFA.validate_transition(curr_state, symbol, user_role="faculty")
                if check.valid:
                    valid_actions.append({
                        "symbol": symbol,
                        "name": name,
                        "target_state": check.next_state,
                        "target_state_name": DFAState.NAMES.get(check.next_state, "")
                    })
            s["allowed_transitions"] = valid_actions

        return jsonify({
            "success": True,
            "subject": subject,
            "date": date_str,
            "is_finalized": is_session_finalized,
            "students": students,
            "total_enrolled": len(students)
        })

@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    """
    DFA Transition Execution Endpoint.
    Validates transition delta(current_state, symbol).
    """
    data = request.get_json() or {}
    student_id = int(data.get("student_id", 0))
    subject_id = int(data.get("subject_id", 0))
    date_str = data.get("date", "")
    symbol = data.get("symbol", "")
    reason = data.get("reason", "").strip()

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    if not student_id or not subject_id or not date_str or not symbol:
        return jsonify({"success": False, "error": "student_id, subject_id, date, and symbol are required."}), 400

    # 1. Fetch current state
    if Database.is_mongo():
        db = Database.get_mongo_db()
        existing = db.attendance.find_one({
            "student_id": student_id,
            "subject_id": subject_id,
            "attendance_date": date_str
        })
        current_state = existing["automata_state"] if existing else DFAState.S0
    else:
        existing = Database.query_one("""
            SELECT * FROM attendance
            WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
        """, (student_id, subject_id, date_str))
        current_state = existing["automata_state"] if existing else DFAState.S0

    # 2. Enforce DFA Transition Rules
    has_audit_reason = bool(reason)
    dfa_res = AttendanceDFA.validate_transition(
        current_state=current_state,
        input_symbol=symbol,
        user_role=user_role,
        has_audit_reason=has_audit_reason
    )

    if not dfa_res.valid:
        return jsonify({
            "success": False,
            "error_type": "DFA_TRANSITION_REJECTED",
            "error": dfa_res.message,
            "current_state": current_state,
            "attempted_symbol": symbol,
            "details": dfa_res.details
        }), 400

    next_state = dfa_res.next_state
    new_status = status_from_state(next_state)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Commit to Active Database Engine
    if Database.is_mongo():
        db = Database.get_mongo_db()
        if existing:
            att_id = existing["id"]
            db.attendance.update_one(
                {"id": att_id},
                {"$set": {
                    "status": new_status,
                    "automata_state": next_state,
                    "marked_by": user_id,
                    "updated_at": datetime.datetime.utcnow()
                }}
            )
        else:
            att_id = MongoDB.get_next_id("attendance")
            db.attendance.insert_one({
                "id": att_id,
                "student_id": student_id,
                "subject_id": subject_id,
                "attendance_date": date_str,
                "status": new_status,
                "automata_state": next_state,
                "marked_by": user_id,
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            })

        log_id = MongoDB.get_next_id("attendance_logs")
        audit_msg = reason or dfa_res.details.get("description", f"Transitioned to {next_state}")
        db.attendance_logs.insert_one({
            "id": log_id,
            "attendance_id": att_id,
            "previous_state": current_state,
            "input_symbol": symbol,
            "next_state": next_state,
            "changed_by": user_id,
            "reason": audit_msg,
            "timestamp": now_str
        })

    else:
        if existing:
            att_id = existing["id"]
            Database.execute("""
                UPDATE attendance
                SET status = %s, automata_state = %s, marked_by = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, next_state, user_id, att_id))
        else:
            att_id = Database.insert_and_get_id("""
                INSERT INTO attendance (student_id, subject_id, attendance_date, status, automata_state, marked_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (student_id, subject_id, date_str, new_status, next_state, user_id))

        audit_msg = reason or dfa_res.details.get("description", f"Transitioned to {next_state}")
        Database.execute("""
            INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (att_id, current_state, symbol, next_state, user_id, audit_msg))

    return jsonify({
        "success": True,
        "message": dfa_res.message,
        "attendance_id": att_id,
        "previous_state": current_state,
        "next_state": next_state,
        "status": new_status,
        "dfa_details": dfa_res.to_dict()
    })

@app.route("/api/attendance/batch", methods=["POST"])
def batch_mark_attendance():
    data = request.get_json() or {}
    subject_id = int(data.get("subject_id", 0))
    date_str = data.get("date")
    symbol = data.get("symbol", "P")

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    if Database.is_mongo():
        db = Database.get_mongo_db()
        enrollments = list(db.enrollments.find({"subject_id": subject_id}))
        if not enrollments:
            return jsonify({"success": False, "error": "No students enrolled in this subject."}), 400

        updated_count = 0
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in enrollments:
            st_id = item["student_id"]
            existing = db.attendance.find_one({
                "student_id": st_id,
                "subject_id": subject_id,
                "attendance_date": date_str
            })
            curr_state = existing["automata_state"] if existing else DFAState.S0
            dfa_res = AttendanceDFA.validate_transition(curr_state, symbol, user_role=user_role)
            if not dfa_res.valid:
                continue

            next_state = dfa_res.next_state
            new_status = status_from_state(next_state)

            if existing:
                att_id = existing["id"]
                db.attendance.update_one(
                    {"id": att_id},
                    {"$set": {"status": new_status, "automata_state": next_state, "marked_by": user_id, "updated_at": datetime.datetime.utcnow()}}
                )
            else:
                att_id = MongoDB.get_next_id("attendance")
                db.attendance.insert_one({
                    "id": att_id,
                    "student_id": st_id,
                    "subject_id": subject_id,
                    "attendance_date": date_str,
                    "status": new_status,
                    "automata_state": next_state,
                    "marked_by": user_id,
                    "created_at": datetime.datetime.utcnow(),
                    "updated_at": datetime.datetime.utcnow()
                })

            log_id = MongoDB.get_next_id("attendance_logs")
            db.attendance_logs.insert_one({
                "id": log_id,
                "attendance_id": att_id,
                "previous_state": curr_state,
                "input_symbol": symbol,
                "next_state": next_state,
                "changed_by": user_id,
                "reason": f"Batch transition: {symbol}",
                "timestamp": now_str
            })
            updated_count += 1

        return jsonify({"success": True, "updated_count": updated_count})

    else:
        # SQLite
        enrollments = Database.query_all("SELECT student_id FROM enrollments WHERE subject_id = %s", (subject_id,))
        updated_count = 0
        for item in enrollments:
            st_id = item["student_id"]
            existing = Database.query_one("""
                SELECT id, automata_state FROM attendance
                WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
            """, (st_id, subject_id, date_str))
            curr_state = existing["automata_state"] if existing else DFAState.S0
            dfa_res = AttendanceDFA.validate_transition(curr_state, symbol, user_role=user_role)
            if not dfa_res.valid: continue

            next_state = dfa_res.next_state
            new_status = status_from_state(next_state)
            if existing:
                att_id = existing["id"]
                Database.execute("""
                    UPDATE attendance SET status = %s, automata_state = %s, marked_by = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
                """, (new_status, next_state, user_id, att_id))
            else:
                att_id = Database.insert_and_get_id("""
                    INSERT INTO attendance (student_id, subject_id, attendance_date, status, automata_state, marked_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (st_id, subject_id, date_str, new_status, next_state, user_id))

            Database.execute("""
                INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (att_id, curr_state, symbol, next_state, user_id, f"Batch transition: {symbol}"))
            updated_count += 1

        return jsonify({"success": True, "updated_count": updated_count})

@app.route("/api/attendance/finalize", methods=["POST"])
def finalize_session():
    data = request.get_json() or {}
    subject_id = int(data.get("subject_id", 0))
    date_str = data.get("date")

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    if Database.is_mongo():
        db = Database.get_mongo_db()
        enrollments = list(db.enrollments.find({"subject_id": subject_id}))
        if not enrollments:
            return jsonify({"success": False, "error": "No students found."}), 400

        unmarked = []
        students = []
        for e in enrollments:
            st_id = e["student_id"]
            att = db.attendance.find_one({"student_id": st_id, "subject_id": subject_id, "attendance_date": date_str})
            curr_state = att["automata_state"] if att else DFAState.S0
            if curr_state == DFAState.S0:
                unmarked.append(st_id)
            students.append({"student_id": st_id, "attendance_id": att["id"] if att else None, "automata_state": curr_state})

        if unmarked:
            return jsonify({
                "success": False,
                "error_type": "DFA_FINALIZATION_REJECTED",
                "error": f"Cannot finalize attendance: {len(unmarked)} student(s) are still in state S0 (Not Marked). Transition δ(S0, F) is undefined. Please mark all students."
            }), 400

        finalized_count = 0
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for s in students:
            curr_state = s["automata_state"]
            if curr_state == DFAState.S4: continue

            dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.F, user_role=user_role)
            if dfa_res.valid:
                att_id = s["attendance_id"]
                db.attendance.update_one(
                    {"id": att_id},
                    {"$set": {"status": "Finalized", "automata_state": "S4", "updated_at": datetime.datetime.utcnow()}}
                )
                log_id = MongoDB.get_next_id("attendance_logs")
                db.attendance_logs.insert_one({
                    "id": log_id,
                    "attendance_id": att_id,
                    "previous_state": curr_state,
                    "input_symbol": "F",
                    "next_state": "S4",
                    "changed_by": user_id,
                    "reason": "Session Finalized via DFA input F",
                    "timestamp": now_str
                })
                finalized_count += 1

        return jsonify({
            "success": True,
            "message": f"Successfully finalized {finalized_count} records into DFA state S4.",
            "finalized_count": finalized_count
        })

    else:
        # SQLite
        students = Database.query_all("""
            SELECT s.id as student_id,
                   COALESCE(a.id, 0) as attendance_id,
                   COALESCE(a.automata_state, 'S0') as automata_state
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = %s AND a.attendance_date = %s
            WHERE e.subject_id = %s
        """, (subject_id, date_str, subject_id))

        unmarked = [s for s in students if s["automata_state"] == DFAState.S0]
        if unmarked:
            return jsonify({
                "success": False,
                "error_type": "DFA_FINALIZATION_REJECTED",
                "error": f"Cannot finalize attendance: {len(unmarked)} student(s) are still in state S0 (Not Marked). DFA transition δ(S0, F) is undefined."
            }), 400

        finalized_count = 0
        for s in students:
            curr_state = s["automata_state"]
            if curr_state == DFAState.S4: continue
            dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.F, user_role=user_role)
            if dfa_res.valid:
                att_id = s["attendance_id"]
                Database.execute("UPDATE attendance SET status = 'Finalized', automata_state = 'S4', updated_at = CURRENT_TIMESTAMP WHERE id = %s", (att_id,))
                Database.execute("INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason) VALUES (%s, %s, %s, %s, %s, %s)", (att_id, curr_state, 'F', 'S4', user_id, "Session Finalized via DFA input F"))
                finalized_count += 1

        return jsonify({
            "success": True,
            "message": f"Successfully finalized {finalized_count} attendance records.",
            "finalized_count": finalized_count
        })

@app.route("/api/attendance/reset", methods=["POST"])
def admin_reset_attendance():
    """Authorized Admin Reset (S4 -> S0) with mandatory audit reason."""
    data = request.get_json() or {}
    attendance_id = int(data.get("attendance_id", 0))
    reason = data.get("reason", "").strip()

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "student"
    user_id = current_user["id"] if current_user else None

    if user_role != "admin":
        return jsonify({
            "success": False,
            "error_type": "UNAUTHORIZED_DFA_RESET",
            "error": "Access Denied: Only administrators have authorization to execute DFA transition δ(S4, R) -> S0."
        }), 403

    if not reason:
        return jsonify({
            "success": False,
            "error_type": "MISSING_AUDIT_REASON",
            "error": "An audit explanation is strictly mandatory when resetting finalized attendance records."
        }), 400

    if Database.is_mongo():
        db = Database.get_mongo_db()
        att = db.attendance.find_one({"id": attendance_id})
        if not att:
            return jsonify({"success": False, "error": "Attendance record not found."}), 404

        curr_state = att["automata_state"]
        dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.R, user_role="admin", has_audit_reason=True)
        if not dfa_res.valid:
            return jsonify({"success": False, "error": dfa_res.message}), 400

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.attendance.update_one(
            {"id": attendance_id},
            {"$set": {"status": "Not Marked", "automata_state": "S0", "updated_at": datetime.datetime.utcnow()}}
        )
        log_id = MongoDB.get_next_id("attendance_logs")
        db.attendance_logs.insert_one({
            "id": log_id,
            "attendance_id": attendance_id,
            "previous_state": curr_state,
            "input_symbol": "R",
            "next_state": "S0",
            "changed_by": user_id,
            "reason": f"Admin Reset: {reason}",
            "timestamp": now_str
        })

        return jsonify({
            "success": True,
            "message": f"Authorized Admin Reset complete: Transitioned {curr_state} -> S0.",
            "previous_state": curr_state,
            "next_state": "S0"
        })

    else:
        # SQLite
        att = Database.query_one("SELECT * FROM attendance WHERE id = %s", (attendance_id,))
        if not att:
            return jsonify({"success": False, "error": "Attendance record not found."}), 404

        curr_state = att["automata_state"]
        dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.R, user_role="admin", has_audit_reason=True)
        if not dfa_res.valid:
            return jsonify({"success": False, "error": dfa_res.message}), 400

        Database.execute("UPDATE attendance SET status = 'Not Marked', automata_state = 'S0', updated_at = CURRENT_TIMESTAMP WHERE id = %s", (attendance_id,))
        Database.execute("INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason) VALUES (%s, %s, %s, %s, %s, %s)", (attendance_id, curr_state, 'R', 'S0', user_id, f"Admin Reset: {reason}"))

        return jsonify({
            "success": True,
            "message": f"Authorized Admin Reset complete: Transitioned {curr_state} -> S0.",
            "previous_state": curr_state,
            "next_state": "S0"
        })

# ==============================================================================
# Reports & CSV Export
# ==============================================================================

@app.route("/api/attendance/reports", methods=["GET"])
def get_attendance_reports():
    dept_id = request.args.get("department_id")
    semester = request.args.get("semester")
    subject_id = request.args.get("subject_id")
    student_id = request.args.get("student_id")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    if Database.is_mongo():
        db = Database.get_mongo_db()
        filter_st = {}
        if dept_id: filter_st["department_id"] = int(dept_id)
        if semester: filter_st["semester"] = int(semester)
        if student_id: filter_st["id"] = int(student_id)

        students = list(db.students.find(filter_st))
        reports = []

        for st in students:
            u = db.users.find_one({"id": st["user_id"]}) or {}
            d = db.departments.find_one({"id": st["department_id"]}) or {}

            # Subjects enrolled
            enroll_filter = {"student_id": st["id"]}
            if subject_id: enroll_filter["subject_id"] = int(subject_id)
            enrolled = list(db.enrollments.find(enroll_filter))

            for en in enrolled:
                sub = db.subjects.find_one({"id": en["subject_id"]})
                if not sub: continue

                att_filter = {"student_id": st["id"], "subject_id": sub["id"]}
                if from_date: att_filter["attendance_date"] = {"$gte": from_date}
                if to_date:
                    att_filter.setdefault("attendance_date", {})["$lte"] = to_date

                att_records = list(db.attendance.find(att_filter))
                total = len(att_records)
                present = sum(1 for a in att_records if a["status"] == "Present" or (a["automata_state"] == "S4" and a["status"] in ["Present", "Finalized"]))
                absent = sum(1 for a in att_records if a["status"] == "Absent")
                late = sum(1 for a in att_records if a["status"] == "Late")

                pct = round((present / total) * 100, 1) if total > 0 else 0.0
                warning = (pct < 75.0) and (total > 0)

                reports.append({
                    "student_id": st["id"],
                    "register_number": st.get("register_number", ""),
                    "student_name": u.get("name", "Student"),
                    "department_code": d.get("department_code", ""),
                    "department_name": d.get("department_name", ""),
                    "semester": st.get("semester", 1),
                    "subject_id": sub["id"],
                    "subject_code": sub["subject_code"],
                    "subject_name": sub["subject_name"],
                    "total_conducted": total,
                    "present_count": present,
                    "absent_count": absent,
                    "late_count": late,
                    "attendance_percentage": pct,
                    "below_threshold": warning
                })

        return jsonify({"success": True, "reports": reports, "count": len(reports)})

    else:
        # SQLite
        where_clauses = ["1=1"]
        params = []
        if dept_id: where_clauses.append("s.department_id = %s"); params.append(dept_id)
        if semester: where_clauses.append("s.semester = %s"); params.append(semester)
        if subject_id: where_clauses.append("a.subject_id = %s"); params.append(subject_id)
        if student_id: where_clauses.append("s.id = %s"); params.append(student_id)
        if from_date: where_clauses.append("a.attendance_date >= %s"); params.append(from_date)
        if to_date: where_clauses.append("a.attendance_date <= %s"); params.append(to_date)

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT s.id as student_id, s.register_number, u.name as student_name,
                   d.department_code, d.department_name, s.semester,
                   sub.id as subject_id, sub.subject_code, sub.subject_name,
                   COUNT(a.id) as total_conducted,
                   SUM(CASE WHEN a.status = 'Present' OR (a.automata_state = 'S4' AND a.status = 'Finalized') THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                   SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_count
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN departments d ON s.department_id = d.id
            JOIN enrollments e ON s.id = e.student_id
            JOIN subjects sub ON e.subject_id = sub.id
            LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = sub.id
            WHERE {where_sql}
            GROUP BY s.id, sub.id
            ORDER BY d.department_code, s.register_number, sub.subject_code
        """
        rows = Database.query_all(query, tuple(params))
        reports = []
        for r in rows:
            total = r["total_conducted"] or 0
            present = r["present_count"] or 0
            absent = r["absent_count"] or 0
            late = r["late_count"] or 0
            percentage = round((present / total) * 100, 1) if total > 0 else 0.0
            warning = (percentage < 75.0) and (total > 0)
            reports.append({
                "student_id": r["student_id"],
                "register_number": r["register_number"],
                "student_name": r["student_name"],
                "department_code": r["department_code"],
                "department_name": r["department_name"],
                "semester": r["semester"],
                "subject_id": r["subject_id"],
                "subject_code": r["subject_code"],
                "subject_name": r["subject_name"],
                "total_conducted": total,
                "present_count": present,
                "absent_count": absent,
                "late_count": late,
                "attendance_percentage": percentage,
                "below_threshold": warning
            })
        return jsonify({"success": True, "reports": reports, "count": len(reports)})

@app.route("/api/attendance/export-csv", methods=["GET"])
def export_attendance_csv():
    reports_resp = get_attendance_reports()
    data = reports_resp.get_json().get("reports", [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Register Number", "Student Name", "Department", "Semester",
        "Subject Code", "Subject Name", "Conducted Classes",
        "Present", "Absent", "Late", "Attendance %", "Warning (< 75%)"
    ])

    for r in data:
        writer.writerow([
            r["register_number"],
            r["student_name"],
            r["department_code"],
            r["semester"],
            r["subject_code"],
            r["subject_name"],
            r["total_conducted"],
            r["present_count"],
            r["absent_count"],
            r["late_count"],
            f"{r['attendance_percentage']}%",
            "CRITICAL WARNING" if r["below_threshold"] else "Satisfactory"
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_report.csv"}
    )

# ==============================================================================
# Role-Based Dashboards
# ==============================================================================

@app.route("/api/dashboard/admin", methods=["GET"])
def admin_dashboard():
    if Database.is_mongo():
        db = Database.get_mongo_db()
        st_count = db.students.count_documents({})
        fac_count = db.faculty.count_documents({})
        dept_count = db.departments.count_documents({})
        sub_count = db.subjects.count_documents({})
        att_count = db.attendance.count_documents({})

        # Department performance
        dept_stats = []
        for d in db.departments.find({}):
            st_ids = [s["id"] for s in db.students.find({"department_id": d["id"]})]
            total_recs = db.attendance.count_documents({"student_id": {"$in": st_ids}})
            pres_recs = db.attendance.count_documents({"student_id": {"$in": st_ids}, "status": "Present"})
            pct = round((pres_recs / total_recs) * 100, 1) if total_recs > 0 else 0.0
            dept_stats.append({
                "department_name": d["department_name"],
                "department_code": d["department_code"],
                "total_records": total_recs,
                "present_count": pres_recs,
                "percentage": pct
            })

        # State distribution
        state_distribution = []
        for st in ["S0", "S1", "S2", "S3", "S4"]:
            c = db.attendance.count_documents({"automata_state": st})
            if c > 0:
                state_distribution.append({"automata_state": st, "count": c})

        # Recent logs
        recent_logs = []
        for l in db.attendance_logs.find({}).sort("id", -1).limit(10):
            att = db.attendance.find_one({"id": l["attendance_id"]}) or {}
            st = db.students.find_one({"id": att.get("student_id")}) or {}
            st_u = db.users.find_one({"id": st.get("user_id")}) or {}
            sub = db.subjects.find_one({"id": att.get("subject_id")}) or {}
            actor = db.users.find_one({"id": l.get("changed_by")}) or {}

            recent_logs.append({
                "id": l["id"],
                "previous_state": l["previous_state"],
                "input_symbol": l["input_symbol"],
                "next_state": l["next_state"],
                "reason": l.get("reason", ""),
                "timestamp": l.get("timestamp", ""),
                "changed_by_name": actor.get("name", "System"),
                "student_name": st_u.get("name", "Student"),
                "register_number": st.get("register_number", ""),
                "subject_code": sub.get("subject_code", "")
            })

        return jsonify({
            "success": True,
            "counts": {
                "students": st_count,
                "faculty": fac_count,
                "departments": dept_count,
                "subjects": sub_count,
                "attendance_records": att_count
            },
            "department_stats": dept_stats,
            "state_distribution": state_distribution,
            "recent_logs": recent_logs
        })

    else:
        # SQLite
        students_count = Database.query_one("SELECT COUNT(*) as count FROM students")["count"]
        faculty_count = Database.query_one("SELECT COUNT(*) as count FROM faculty")["count"]
        depts_count = Database.query_one("SELECT COUNT(*) as count FROM departments")["count"]
        subjects_count = Database.query_one("SELECT COUNT(*) as count FROM subjects")["count"]
        attendance_count = Database.query_one("SELECT COUNT(*) as count FROM attendance")["count"]

        dept_stats = Database.query_all("""
            SELECT d.department_name, d.department_code,
                   COUNT(a.id) as total_records,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count
            FROM departments d
            LEFT JOIN students s ON s.department_id = d.id
            LEFT JOIN attendance a ON a.student_id = s.id
            GROUP BY d.id
        """)
        for ds in dept_stats:
            total = ds["total_records"]
            present = ds["present_count"] or 0
            ds["percentage"] = round((present / total) * 100, 1) if total > 0 else 0.0

        recent_logs = Database.query_all("""
            SELECT al.id, al.previous_state, al.input_symbol, al.next_state, al.reason, al.timestamp,
                   u.name as changed_by_name, st_u.name as student_name, st.register_number, sub.subject_code
            FROM attendance_logs al
            LEFT JOIN users u ON al.changed_by = u.id
            JOIN attendance a ON al.attendance_id = a.id
            JOIN students st ON a.student_id = st.id
            JOIN users st_u ON st.user_id = st_u.id
            JOIN subjects sub ON a.subject_id = sub.id
            ORDER BY al.id DESC LIMIT 10
        """)

        state_distribution = Database.query_all("""
            SELECT automata_state, COUNT(*) as count FROM attendance GROUP BY automata_state
        """)

        return jsonify({
            "success": True,
            "counts": {
                "students": students_count,
                "faculty": faculty_count,
                "departments": depts_count,
                "subjects": subjects_count,
                "attendance_records": attendance_count
            },
            "department_stats": dept_stats,
            "state_distribution": state_distribution,
            "recent_logs": recent_logs
        })

@app.route("/api/dashboard/faculty", methods=["GET"])
def faculty_dashboard():
    user = get_current_user_from_header()
    user_id = int(user["id"]) if user else int(request.args.get("user_id", 0))
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    if Database.is_mongo():
        db = Database.get_mongo_db()
        fac = db.faculty.find_one({"user_id": user_id})
        if not fac:
            return jsonify({"success": False, "error": "Faculty record not found."}), 404

        assigned = list(db.faculty_subjects.find({"faculty_id": fac["id"]}))
        subjects_list = []
        for a in assigned:
            sub = db.subjects.find_one({"id": a["subject_id"]})
            if not sub: continue
            dept = db.departments.find_one({"id": sub["department_id"]}) or {}
            enrolled_count = db.enrollments.count_documents({"subject_id": sub["id"]})
            today_att = list(db.attendance.find({"subject_id": sub["id"], "attendance_date": today_str}))
            today_state = today_att[0]["automata_state"] if today_att else "S0"

            subjects_list.append({
                "id": sub["id"],
                "subject_name": sub["subject_name"],
                "subject_code": sub["subject_code"],
                "semester": sub.get("semester", 1),
                "credits": sub.get("credits", 3),
                "department_code": dept.get("department_code", ""),
                "enrolled_students": enrolled_count,
                "today_marked_count": len(today_att),
                "today_state": today_state
            })

        return jsonify({"success": True, "today": today_str, "subjects": subjects_list})

    else:
        # SQLite
        fac = Database.query_one("SELECT id, department_id FROM faculty WHERE user_id = %s", (user_id,))
        if not fac:
            return jsonify({"success": False, "error": "Faculty record not found."}), 404

        faculty_id = fac["id"]
        assigned_subjects = Database.query_all("""
            SELECT sub.id, sub.subject_name, sub.subject_code, sub.semester, sub.credits,
                   d.department_code,
                   (SELECT COUNT(*) FROM enrollments WHERE subject_id = sub.id) as enrolled_students,
                   (SELECT COUNT(*) FROM attendance WHERE subject_id = sub.id AND attendance_date = %s) as today_marked_count,
                   (SELECT automata_state FROM attendance WHERE subject_id = sub.id AND attendance_date = %s LIMIT 1) as today_state
            FROM faculty_subjects fs
            JOIN subjects sub ON fs.subject_id = sub.id
            JOIN departments d ON sub.department_id = d.id
            WHERE fs.faculty_id = %s
        """, (today_str, today_str, faculty_id))

        return jsonify({"success": True, "today": today_str, "subjects": assigned_subjects})

@app.route("/api/dashboard/student", methods=["GET"])
def student_dashboard():
    user = get_current_user_from_header()
    user_id = int(user["id"]) if user else int(request.args.get("user_id", 0))

    if Database.is_mongo():
        db = Database.get_mongo_db()
        stud = db.students.find_one({"user_id": user_id})
        if not stud:
            return jsonify({"success": False, "error": "Student record not found."}), 404

        u = db.users.find_one({"id": user_id}) or {}
        d = db.departments.find_one({"id": stud["department_id"]}) or {}

        profile = {
            "student_id": stud["id"],
            "register_number": stud.get("register_number", ""),
            "semester": stud.get("semester", 1),
            "department_name": d.get("department_name", ""),
            "department_code": d.get("department_code", ""),
            "name": u.get("name", ""),
            "email": u.get("email", "")
        }

        enrolled = list(db.enrollments.find({"student_id": stud["id"]}))
        subjects_list = []
        total_classes = 0
        total_present = 0
        total_absent = 0
        total_late = 0

        for en in enrolled:
            sub = db.subjects.find_one({"id": en["subject_id"]})
            if not sub: continue
            att_recs = list(db.attendance.find({"student_id": stud["id"], "subject_id": sub["id"]}))
            tc = len(att_recs)
            tp = sum(1 for a in att_recs if a["status"] == "Present" or (a["automata_state"] == "S4" and a["status"] in ["Present", "Finalized"]))
            ta = sum(1 for a in att_recs if a["status"] == "Absent")
            tl = sum(1 for a in att_recs if a["status"] == "Late")

            pct = round((tp / tc) * 100, 1) if tc > 0 else 0.0
            total_classes += tc
            total_present += tp
            total_absent += ta
            total_late += tl

            subjects_list.append({
                "subject_id": sub["id"],
                "subject_name": sub["subject_name"],
                "subject_code": sub["subject_code"],
                "semester": sub.get("semester", 1),
                "total_conducted": tc,
                "present_count": tp,
                "absent_count": ta,
                "late_count": tl,
                "percentage": pct,
                "warning": (pct < 75.0) and (tc > 0)
            })

        overall_percentage = round((total_present / total_classes) * 100, 1) if total_classes > 0 else 0.0
        needs_warning = (overall_percentage < 75.0) and (total_classes > 0)

        # Monthly trend
        att_all = list(db.attendance.find({"student_id": stud["id"]}))
        month_map = {}
        for a in att_all:
            m = a["attendance_date"][:7]
            month_map.setdefault(m, {"total": 0, "present": 0})
            month_map[m]["total"] += 1
            if a["status"] in ["Present", "Finalized"]:
                month_map[m]["present"] += 1

        monthly_trend = [{"month": k, "total": v["total"], "present": v["present"]} for k, v in sorted(month_map.items())]

        return jsonify({
            "success": True,
            "profile": profile,
            "summary": {
                "overall_percentage": overall_percentage,
                "total_conducted": total_classes,
                "present": total_present,
                "absent": total_absent,
                "late": total_late,
                "warning": needs_warning
            },
            "subjects": subjects_list,
            "monthly_trend": monthly_trend
        })

    else:
        # SQLite
        stud = Database.query_one("""
            SELECT s.id as student_id, s.register_number, s.semester,
                   d.department_name, d.department_code, u.name, u.email
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN departments d ON s.department_id = d.id
            WHERE s.user_id = %s
        """, (user_id,))
        if not stud:
            return jsonify({"success": False, "error": "Student record not found."}), 404

        student_id = stud["student_id"]
        subject_stats = Database.query_all("""
            SELECT sub.id as subject_id, sub.subject_name, sub.subject_code, sub.semester,
                   COUNT(a.id) as total_conducted,
                   SUM(CASE WHEN a.status = 'Present' OR (a.automata_state = 'S4' AND a.status = 'Finalized') THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                   SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_count
            FROM enrollments e
            JOIN subjects sub ON e.subject_id = sub.id
            LEFT JOIN attendance a ON a.student_id = %s AND a.subject_id = sub.id
            WHERE e.student_id = %s
            GROUP BY sub.id
        """, (student_id, student_id))

        total_classes = 0
        total_present = 0
        total_absent = 0
        total_late = 0
        subjects_list = []
        for s in subject_stats:
            tc = s["total_conducted"] or 0
            tp = s["present_count"] or 0
            ta = s["absent_count"] or 0
            tl = s["late_count"] or 0
            pct = round((tp / tc) * 100, 1) if tc > 0 else 0.0
            total_classes += tc
            total_present += tp
            total_absent += ta
            total_late += tl
            subjects_list.append({
                "subject_id": s["subject_id"],
                "subject_name": s["subject_name"],
                "subject_code": s["subject_code"],
                "semester": s["semester"],
                "total_conducted": tc,
                "present_count": tp,
                "absent_count": ta,
                "late_count": tl,
                "percentage": pct,
                "warning": (pct < 75.0) and (tc > 0)
            })

        overall_percentage = round((total_present / total_classes) * 100, 1) if total_classes > 0 else 0.0
        needs_warning = (overall_percentage < 75.0) and (total_classes > 0)

        monthly_trend = Database.query_all("""
            SELECT strftime('%Y-%m', attendance_date) as month,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'Present' OR automata_state = 'S4' THEN 1 ELSE 0 END) as present
            FROM attendance
            WHERE student_id = %s
            GROUP BY strftime('%Y-%m', attendance_date)
            ORDER BY month ASC
        """, (student_id,))

        return jsonify({
            "success": True,
            "profile": stud,
            "summary": {
                "overall_percentage": overall_percentage,
                "total_conducted": total_classes,
                "present": total_present,
                "absent": total_absent,
                "late": total_late,
                "warning": needs_warning
            },
            "subjects": subjects_list,
            "monthly_trend": monthly_trend
        })

# ==============================================================================
# Admin CRUD APIs (Departments, Faculty, Students, Subjects, Audit Logs)
# ==============================================================================

@app.route("/api/admin/departments", methods=["GET", "POST"])
def manage_departments():
    if request.method == "GET":
        if Database.is_mongo():
            depts = list(Database.get_mongo_db().departments.find({}, {"_id": 0}).sort("department_name", 1))
        else:
            depts = Database.query_all("SELECT * FROM departments ORDER BY department_name")
        return jsonify({"success": True, "departments": depts})

    data = request.get_json() or {}
    name = data.get("department_name", "").strip()
    code = data.get("department_code", "").strip().upper()
    if not name or not code:
        return jsonify({"success": False, "error": "Name and code required."}), 400

    if Database.is_mongo():
        db = Database.get_mongo_db()
        dept_id = MongoDB.get_next_id("departments")
        db.departments.insert_one({
            "id": dept_id,
            "department_name": name,
            "department_code": code,
            "created_at": datetime.datetime.utcnow()
        })
    else:
        dept_id = Database.insert_and_get_id(
            "INSERT INTO departments (department_name, department_code) VALUES (%s, %s)",
            (name, code)
        )
    return jsonify({"success": True, "id": dept_id, "message": "Department created."})

@app.route("/api/admin/departments/<int:id>", methods=["DELETE"])
def delete_department(id):
    if Database.is_mongo():
        Database.get_mongo_db().departments.delete_one({"id": id})
    else:
        Database.execute("DELETE FROM departments WHERE id = %s", (id,))
    return jsonify({"success": True, "message": "Department deleted."})

@app.route("/api/admin/faculty", methods=["GET", "POST"])
def manage_faculty():
    if request.method == "GET":
        if Database.is_mongo():
            db = Database.get_mongo_db()
            fac_list = []
            for f in db.faculty.find({}):
                u = db.users.find_one({"id": f["user_id"]}) or {}
                d = db.departments.find_one({"id": f["department_id"]}) or {}
                sub_count = db.faculty_subjects.count_documents({"faculty_id": f["id"]})
                fac_list.append({
                    "id": f["id"],
                    "user_id": f["user_id"],
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "designation": f.get("designation", ""),
                    "department_id": f["department_id"],
                    "department_name": d.get("department_name", ""),
                    "department_code": d.get("department_code", ""),
                    "subjects_count": sub_count
                })
            return jsonify({"success": True, "faculty": fac_list})
        else:
            fac = Database.query_all("""
                SELECT f.id, f.user_id, u.name, u.email, f.designation, f.department_id,
                       d.department_name, d.department_code,
                       (SELECT COUNT(*) FROM faculty_subjects WHERE faculty_id = f.id) as subjects_count
                FROM faculty f
                JOIN users u ON f.user_id = u.id
                JOIN departments d ON f.department_id = d.id
                ORDER BY u.name
            """)
            return jsonify({"success": True, "faculty": fac})

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    dept_id = int(data.get("department_id", 1))
    designation = data.get("designation", "Assistant Professor")

    if Database.is_mongo():
        db = Database.get_mongo_db()
        u_id = MongoDB.get_next_id("users")
        db.users.insert_one({
            "id": u_id,
            "name": name,
            "email": email,
            "password": generate_password_hash("faculty123"),
            "role": "faculty",
            "created_at": datetime.datetime.utcnow()
        })
        f_id = MongoDB.get_next_id("faculty")
        db.faculty.insert_one({
            "id": f_id,
            "user_id": u_id,
            "department_id": dept_id,
            "designation": designation,
            "created_at": datetime.datetime.utcnow()
        })
    else:
        u_id = Database.insert_and_get_id(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'faculty')",
            (name, email, generate_password_hash("faculty123"))
        )
        f_id = Database.insert_and_get_id(
            "INSERT INTO faculty (user_id, department_id, designation) VALUES (%s, %s, %s)",
            (u_id, dept_id, designation)
        )
    return jsonify({"success": True, "faculty_id": f_id, "message": "Faculty registered."})

@app.route("/api/admin/faculty/<int:id>", methods=["DELETE"])
def delete_faculty(id):
    if Database.is_mongo():
        db = Database.get_mongo_db()
        fac = db.faculty.find_one({"id": id})
        if fac:
            db.users.delete_one({"id": fac["user_id"]})
            db.faculty.delete_one({"id": id})
    else:
        fac = Database.query_one("SELECT user_id FROM faculty WHERE id = %s", (id,))
        if fac: Database.execute("DELETE FROM users WHERE id = %s", (fac["user_id"],))
    return jsonify({"success": True, "message": "Faculty deleted."})

@app.route("/api/admin/students", methods=["GET", "POST"])
def manage_students():
    if request.method == "GET":
        if Database.is_mongo():
            db = Database.get_mongo_db()
            st_list = []
            for s in db.students.find({}):
                u = db.users.find_one({"id": s["user_id"]}) or {}
                d = db.departments.find_one({"id": s["department_id"]}) or {}
                enrolled_count = db.enrollments.count_documents({"student_id": s["id"]})
                st_list.append({
                    "id": s["id"],
                    "user_id": s["user_id"],
                    "register_number": s.get("register_number", ""),
                    "semester": s.get("semester", 1),
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "department_name": d.get("department_name", ""),
                    "department_code": d.get("department_code", ""),
                    "department_id": s["department_id"],
                    "enrolled_subjects": enrolled_count
                })
            return jsonify({"success": True, "students": st_list})
        else:
            students = Database.query_all("""
                SELECT s.id, s.user_id, s.register_number, s.semester, u.name, u.email,
                       d.department_name, d.department_code, s.department_id,
                       (SELECT COUNT(*) FROM enrollments WHERE student_id = s.id) as enrolled_subjects
                FROM students s
                JOIN users u ON s.user_id = u.id
                JOIN departments d ON s.department_id = d.id
                ORDER BY s.register_number
            """)
            return jsonify({"success": True, "students": students})

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    reg_no = data.get("register_number", "").strip().upper()
    dept_id = int(data.get("department_id", 1))
    semester = int(data.get("semester", 1))

    if Database.is_mongo():
        db = Database.get_mongo_db()
        u_id = MongoDB.get_next_id("users")
        db.users.insert_one({
            "id": u_id,
            "name": name,
            "email": email,
            "password": generate_password_hash("student123"),
            "role": "student",
            "created_at": datetime.datetime.utcnow()
        })
        s_id = MongoDB.get_next_id("students")
        db.students.insert_one({
            "id": s_id,
            "user_id": u_id,
            "register_number": reg_no,
            "department_id": dept_id,
            "semester": semester,
            "created_at": datetime.datetime.utcnow()
        })
    else:
        u_id = Database.insert_and_get_id(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'student')",
            (name, email, generate_password_hash("student123"))
        )
        s_id = Database.insert_and_get_id(
            "INSERT INTO students (user_id, register_number, department_id, semester) VALUES (%s, %s, %s, %s)",
            (u_id, reg_no, dept_id, semester)
        )
    return jsonify({"success": True, "student_id": s_id, "message": "Student created."})

@app.route("/api/admin/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    if Database.is_mongo():
        db = Database.get_mongo_db()
        st = db.students.find_one({"id": id})
        if st:
            db.users.delete_one({"id": st["user_id"]})
            db.students.delete_one({"id": id})
            db.enrollments.delete_many({"student_id": id})
    else:
        st = Database.query_one("SELECT user_id FROM students WHERE id = %s", (id,))
        if st: Database.execute("DELETE FROM users WHERE id = %s", (st["user_id"],))
    return jsonify({"success": True, "message": "Student deleted."})

@app.route("/api/admin/subjects", methods=["GET", "POST"])
def manage_subjects():
    if request.method == "GET":
        dept_id = request.args.get("department_id")
        if Database.is_mongo():
            db = Database.get_mongo_db()
            f = {"department_id": int(dept_id)} if dept_id else {}
            sub_list = []
            for sub in db.subjects.find(f):
                d = db.departments.find_one({"id": sub["department_id"]}) or {}
                enrolled = db.enrollments.count_documents({"subject_id": sub["id"]})
                fac_sub = db.faculty_subjects.find_one({"subject_id": sub["id"]})
                fac_name = "Unassigned"
                if fac_sub:
                    fac = db.faculty.find_one({"id": fac_sub["faculty_id"]})
                    if fac:
                        u = db.users.find_one({"id": fac["user_id"]})
                        if u: fac_name = u["name"]

                sub_list.append({
                    "id": sub["id"],
                    "subject_name": sub["subject_name"],
                    "subject_code": sub["subject_code"],
                    "department_id": sub["department_id"],
                    "department_name": d.get("department_name", ""),
                    "department_code": d.get("department_code", ""),
                    "semester": sub.get("semester", 1),
                    "credits": sub.get("credits", 3),
                    "enrolled_students": enrolled,
                    "assigned_faculty_name": fac_name
                })
            return jsonify({"success": True, "subjects": sub_list})
        else:
            sql = """
                SELECT sub.*, d.department_name, d.department_code,
                       (SELECT COUNT(*) FROM enrollments WHERE subject_id = sub.id) as enrolled_students,
                       (SELECT u.name FROM faculty_subjects fs
                        JOIN faculty f ON fs.faculty_id = f.id
                        JOIN users u ON f.user_id = u.id
                        WHERE fs.subject_id = sub.id LIMIT 1) as assigned_faculty_name
                FROM subjects sub
                JOIN departments d ON sub.department_id = d.id
            """
            subjects = Database.query_all(sql + (" WHERE sub.department_id = %s" if dept_id else ""), (dept_id,) if dept_id else ())
            return jsonify({"success": True, "subjects": subjects})

    data = request.get_json() or {}
    name = data.get("subject_name", "").strip()
    code = data.get("subject_code", "").strip().upper()
    dept_id = int(data.get("department_id", 1))
    semester = int(data.get("semester", 1))
    credits = int(data.get("credits", 3))

    if Database.is_mongo():
        db = Database.get_mongo_db()
        s_id = MongoDB.get_next_id("subjects")
        db.subjects.insert_one({
            "id": s_id,
            "subject_name": name,
            "subject_code": code,
            "department_id": dept_id,
            "semester": semester,
            "credits": credits,
            "created_at": datetime.datetime.utcnow()
        })
    else:
        s_id = Database.insert_and_get_id("""
            INSERT INTO subjects (subject_name, subject_code, department_id, semester, credits)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, code, dept_id, semester, credits))

    return jsonify({"success": True, "subject_id": s_id, "message": "Subject created."})

@app.route("/api/admin/subjects/<int:id>", methods=["DELETE"])
def delete_subject(id):
    if Database.is_mongo():
        Database.get_mongo_db().subjects.delete_one({"id": id})
    else:
        Database.execute("DELETE FROM subjects WHERE id = %s", (id,))
    return jsonify({"success": True, "message": "Subject deleted."})

@app.route("/api/admin/audit-logs", methods=["GET"])
def get_audit_logs():
    limit = int(request.args.get("limit", 100))
    if Database.is_mongo():
        db = Database.get_mongo_db()
        logs = []
        for l in db.attendance_logs.find({}).sort("id", -1).limit(limit):
            att = db.attendance.find_one({"id": l["attendance_id"]}) or {}
            st = db.students.find_one({"id": att.get("student_id")}) or {}
            st_u = db.users.find_one({"id": st.get("user_id")}) or {}
            sub = db.subjects.find_one({"id": att.get("subject_id")}) or {}
            actor = db.users.find_one({"id": l.get("changed_by")}) or {}

            logs.append({
                "id": l["id"],
                "attendance_id": l["attendance_id"],
                "previous_state": l["previous_state"],
                "input_symbol": l["input_symbol"],
                "next_state": l["next_state"],
                "reason": l.get("reason", ""),
                "timestamp": l.get("timestamp", ""),
                "attendance_date": att.get("attendance_date", ""),
                "changed_by_name": actor.get("name", "System"),
                "changed_by_role": actor.get("role", "admin"),
                "student_name": st_u.get("name", "Student"),
                "register_number": st.get("register_number", ""),
                "subject_code": sub.get("subject_code", ""),
                "subject_name": sub.get("subject_name", "")
            })
        return jsonify({"success": True, "logs": logs, "count": len(logs)})

    else:
        # SQLite
        logs = Database.query_all(f"""
            SELECT al.*, u.name as changed_by_name, u.role as changed_by_role,
                   st_u.name as student_name, st.register_number, sub.subject_code, sub.subject_name,
                   a.attendance_date
            FROM attendance_logs al
            LEFT JOIN users u ON al.changed_by = u.id
            JOIN attendance a ON al.attendance_id = a.id
            JOIN students st ON a.student_id = st.id
            JOIN users st_u ON st.user_id = st_u.id
            JOIN subjects sub ON a.subject_id = sub.id
            ORDER BY al.id DESC LIMIT {limit}
        """)
        return jsonify({"success": True, "logs": logs, "count": len(logs)})

# ==============================================================================
# Single-Page Frontend Server Route
# ==============================================================================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    static_folder = app.static_folder
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    return send_from_directory(static_folder, "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================================")
    print(f"  AUTOMATED ATTENDANCE MANAGEMENT SYSTEM USING FINITE AUTOMATA    ")
    print(f"  Active Engine: {Database.get_active_engine().upper()}          ")
    print(f"  Server running at: http://127.0.0.1:{port}                     ")
    print(f"==================================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
