"""
Automated Attendance Management System Using Finite Automata
Flask RESTful Backend Application & Static Asset Server
"""

import os
import sys
import datetime
import io
import csv
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(__file__))

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
    """Extract authenticated user info passed in headers or query (mock/session token handling)."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        # Fallback to query param for exports
        user_id = request.args.get("user_id")
    if user_id:
        user = Database.query_one("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
        return user
    return None

def status_from_state(state: str) -> str:
    """Map DFA state to user-friendly status."""
    mapping = {
        DFAState.S0: "Not Marked",
        DFAState.S1: "Present",
        DFAState.S2: "Absent",
        DFAState.S3: "Late",
        DFAState.S4: "Finalized"
    }
    return mapping.get(state, "Not Marked")

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
        if fac:
            extra_info = fac
    elif role == "student":
        stud = Database.query_one("""
            SELECT s.id as student_id, s.register_number, s.department_id, d.department_name, d.department_code, s.semester
            FROM students s
            JOIN departments d ON s.department_id = d.id
            WHERE s.user_id = %s
        """, (user["id"],))
        if stud:
            extra_info = stud

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
    """Return preconfigured demo accounts for convenient testing."""
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
    """Returns formal grammar and visual definition of the attendance DFA."""
    return jsonify({
        "success": True,
        "dfa": AttendanceDFA.get_formal_definition()
    })

@app.route("/api/dfa/simulate", methods=["POST"])
def simulate_dfa():
    """Interactive DFA simulator for arbitrary input sequences."""
    data = request.get_json() or {}
    initial_state = data.get("initial_state", DFAState.S0)
    sequence = data.get("sequence", [])
    role = data.get("role", "faculty")

    result = AttendanceDFA.simulate_sequence(initial_state, sequence, role=role)
    return jsonify({"success": True, "simulation": result})

# ==============================================================================
# Attendance Marking & Finite Automata Validation
# ==============================================================================

@app.route("/api/attendance/sheet", methods=["GET"])
def get_attendance_sheet():
    """
    Returns the attendance worksheet for a specific subject and date.
    Calculates existing DFA states or defaults to S0 (Not Marked).
    """
    subject_id = request.args.get("subject_id")
    date_str = request.args.get("date")

    if not subject_id or not date_str:
        return jsonify({"success": False, "error": "subject_id and date are required."}), 400

    subject = Database.query_one("SELECT * FROM subjects WHERE id = %s", (subject_id,))
    if not subject:
        return jsonify({"success": False, "error": "Subject not found."}), 404

    # Fetch enrolled students
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

    # Determine if entire session is finalized
    is_session_finalized = any(s["automata_state"] == DFAState.S4 for s in students) if students else False

    # For each student, include valid next DFA actions
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
    Core DFA Transition Endpoint.
    Validates transition delta(current_state, symbol).
    Rejects illegal operations mathematically and logs every valid transition.
    """
    data = request.get_json() or {}
    student_id = data.get("student_id")
    subject_id = data.get("subject_id")
    date_str = data.get("date")
    symbol = data.get("symbol") # P, A, L, F, R
    reason = data.get("reason", "").strip()

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    if not student_id or not subject_id or not date_str or not symbol:
        return jsonify({"success": False, "error": "student_id, subject_id, date, and symbol are required."}), 400

    # Look up existing attendance record
    existing = Database.query_one("""
        SELECT * FROM attendance
        WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
    """, (student_id, subject_id, date_str))

    current_state = existing["automata_state"] if existing else DFAState.S0

    # Execute DFA Transition Validation
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

    # Persist attendance record
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

    # Audit log the DFA transition
    audit_msg = reason if reason else dfa_res.details.get("description", f"Transitioned to {next_state}")
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
    """
    Batch mark all enrolled students with a given symbol (e.g. mark all Present 'P').
    Every single record is verified through the DFA engine.
    """
    data = request.get_json() or {}
    subject_id = data.get("subject_id")
    date_str = data.get("date")
    symbol = data.get("symbol", "P")

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    # Get all enrollments
    enrollments = Database.query_all("SELECT student_id FROM enrollments WHERE subject_id = %s", (subject_id,))
    if not enrollments:
        return jsonify({"success": False, "error": "No students enrolled in this subject."}), 400

    updated_count = 0
    rejected_count = 0
    errors = []

    for item in enrollments:
        st_id = item["student_id"]
        existing = Database.query_one("""
            SELECT id, automata_state FROM attendance
            WHERE student_id = %s AND subject_id = %s AND attendance_date = %s
        """, (st_id, subject_id, date_str))

        curr_state = existing["automata_state"] if existing else DFAState.S0
        dfa_res = AttendanceDFA.validate_transition(curr_state, symbol, user_role=user_role)

        if not dfa_res.valid:
            rejected_count += 1
            errors.append(f"Student ID {st_id}: {dfa_res.message}")
            continue

        next_state = dfa_res.next_state
        new_status = status_from_state(next_state)

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
            """, (st_id, subject_id, date_str, new_status, next_state, user_id))

        Database.execute("""
            INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (att_id, curr_state, symbol, next_state, user_id, f"Batch transition: {symbol}"))
        updated_count += 1

    return jsonify({
        "success": True,
        "updated_count": updated_count,
        "rejected_count": rejected_count,
        "errors": errors
    })

@app.route("/api/attendance/finalize", methods=["POST"])
def finalize_session():
    """
    Finalize session attendance using DFA symbol 'F'.
    Locks all records into accepting state S4.
    Rejects if any student is still in S0 (unmarked).
    """
    data = request.get_json() or {}
    subject_id = data.get("subject_id")
    date_str = data.get("date")

    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    # Retrieve all enrolled students and their attendance
    students = Database.query_all("""
        SELECT s.id as student_id,
               COALESCE(a.id, 0) as attendance_id,
               COALESCE(a.automata_state, 'S0') as automata_state
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = %s AND a.attendance_date = %s
        WHERE e.subject_id = %s
    """, (subject_id, date_str, subject_id))

    if not students:
        return jsonify({"success": False, "error": "No students found for this subject."}), 400

    # Verify no student is unmarked (S0)
    unmarked = [s for s in students if s["automata_state"] == DFAState.S0]
    if unmarked:
        return jsonify({
            "success": False,
            "error_type": "DFA_FINALIZATION_REJECTED",
            "error": f"Cannot finalize attendance: {len(unmarked)} student(s) are still in state S0 (Not Marked). DFA transition δ(S0, F) is undefined. Please mark all students before finalization."
        }), 400

    # Finalize each student
    finalized_count = 0
    for s in students:
        curr_state = s["automata_state"]
        if curr_state == DFAState.S4:
            continue # already finalized

        dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.F, user_role=user_role)
        if dfa_res.valid:
            att_id = s["attendance_id"]
            Database.execute("""
                UPDATE attendance
                SET status = 'Finalized', automata_state = 'S4', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (att_id,))

            Database.execute("""
                INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (att_id, curr_state, DFAAlphabet.F, DFAState.S4, user_id, "Session Finalized via DFA input F"))
            finalized_count += 1

    return jsonify({
        "success": True,
        "message": f"Successfully finalized {finalized_count} attendance records. All records are now locked in DFA state S4.",
        "finalized_count": finalized_count
    })

@app.route("/api/attendance/reset", methods=["POST"])
def admin_reset_attendance():
    """
    Authorized Admin Reset (S4 -> S0).
    Requires 'admin' role and a valid audit reason.
    """
    data = request.get_json() or {}
    attendance_id = data.get("attendance_id")
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

    att = Database.query_one("SELECT * FROM attendance WHERE id = %s", (attendance_id,))
    if not att:
        return jsonify({"success": False, "error": "Attendance record not found."}), 404

    curr_state = att["automata_state"]
    dfa_res = AttendanceDFA.validate_transition(curr_state, DFAAlphabet.R, user_role="admin", has_audit_reason=True)
    if not dfa_res.valid:
        return jsonify({"success": False, "error": dfa_res.message}), 400

    Database.execute("""
        UPDATE attendance
        SET status = 'Not Marked', automata_state = 'S0', updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (attendance_id,))

    Database.execute("""
        INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (attendance_id, curr_state, DFAAlphabet.R, DFAState.S0, user_id, f"Admin Reset: {reason}"))

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
    """
    Comprehensive attendance analytics with filters:
    department_id, semester, subject_id, student_id, from_date, to_date.
    Calculates percentage = (Present Classes / Total Conducted Classes) * 100.
    Identifies students with < 75% attendance.
    """
    dept_id = request.args.get("department_id")
    semester = request.args.get("semester")
    subject_id = request.args.get("subject_id")
    student_id = request.args.get("student_id")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    where_clauses = ["1=1"]
    params = []

    if dept_id:
        where_clauses.append("s.department_id = %s")
        params.append(dept_id)
    if semester:
        where_clauses.append("s.semester = %s")
        params.append(semester)
    if subject_id:
        where_clauses.append("a.subject_id = %s")
        params.append(subject_id)
    if student_id:
        where_clauses.append("s.id = %s")
        params.append(student_id)
    if from_date:
        where_clauses.append("a.attendance_date >= %s")
        params.append(from_date)
    if to_date:
        where_clauses.append("a.attendance_date <= %s")
        params.append(to_date)

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            s.id as student_id,
            s.register_number,
            u.name as student_name,
            d.department_code,
            d.department_name,
            s.semester,
            sub.id as subject_id,
            sub.subject_code,
            sub.subject_name,
            COUNT(a.id) as total_conducted,
            SUM(CASE WHEN a.status = 'Present' OR (a.automata_state = 'S4' AND a.status = 'Finalized' AND al.first_status = 'Present') THEN 1
                     WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
            SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
            SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_count
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN departments d ON s.department_id = d.id
        JOIN enrollments e ON s.id = e.student_id
        JOIN subjects sub ON e.subject_id = sub.id
        LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = sub.id
        LEFT JOIN (
            -- Fetch original status marked before finalization
            SELECT attendance_id,
                   CASE WHEN input_symbol = 'P' THEN 'Present'
                        WHEN input_symbol = 'A' THEN 'Absent'
                        WHEN input_symbol = 'L' THEN 'Late'
                        ELSE 'Present' END as first_status
            FROM attendance_logs
            WHERE input_symbol IN ('P', 'A', 'L')
            GROUP BY attendance_id
        ) al ON a.id = al.attendance_id
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
    """Generates downloadable CSV for filtered attendance data."""
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
    """Stats and analytics for Admin."""
    students_count = Database.query_one("SELECT COUNT(*) as count FROM students")["count"]
    faculty_count = Database.query_one("SELECT COUNT(*) as count FROM faculty")["count"]
    depts_count = Database.query_one("SELECT COUNT(*) as count FROM departments")["count"]
    subjects_count = Database.query_one("SELECT COUNT(*) as count FROM subjects")["count"]
    attendance_count = Database.query_one("SELECT COUNT(*) as count FROM attendance")["count"]

    # Department-wise attendance calculation
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

    # Recent DFA activity logs
    recent_logs = Database.query_all("""
        SELECT al.id, al.previous_state, al.input_symbol, al.next_state, al.reason, al.timestamp,
               u.name as changed_by_name,
               st_u.name as student_name,
               st.register_number,
               sub.subject_code
        FROM attendance_logs al
        LEFT JOIN users u ON al.changed_by = u.id
        JOIN attendance a ON al.attendance_id = a.id
        JOIN students st ON a.student_id = st.id
        JOIN users st_u ON st.user_id = st_u.id
        JOIN subjects sub ON a.subject_id = sub.id
        ORDER BY al.id DESC
        LIMIT 10
    """)

    # DFA state distribution across active database
    state_distribution = Database.query_all("""
        SELECT automata_state, COUNT(*) as count
        FROM attendance
        GROUP BY automata_state
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
    """Faculty dashboard data: assigned subjects, today's schedule, stats."""
    user = get_current_user_from_header()
    user_id = user["id"] if user else request.args.get("user_id")

    fac = Database.query_one("SELECT id, department_id FROM faculty WHERE user_id = %s", (user_id,))
    if not fac:
        return jsonify({"success": False, "error": "Faculty record not found."}), 404

    faculty_id = fac["id"]
    today_str = datetime.date.today().strftime("%Y-%m-%d")

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

    return jsonify({
        "success": True,
        "today": today_str,
        "subjects": assigned_subjects
    })

@app.route("/api/dashboard/student", methods=["GET"])
def student_dashboard():
    """Student dashboard data: overall percentage, subject-wise cards, warning, monthly stats."""
    user = get_current_user_from_header()
    user_id = user["id"] if user else request.args.get("user_id")

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

    # Subject wise stats
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

    # Monthly attendance trend
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
# Admin CRUD APIs (Departments, Faculty, Students, Subjects)
# ==============================================================================

# 1. Departments
@app.route("/api/admin/departments", methods=["GET", "POST"])
def manage_departments():
    if request.method == "GET":
        depts = Database.query_all("SELECT * FROM departments ORDER BY department_name")
        return jsonify({"success": True, "departments": depts})

    data = request.get_json() or {}
    name = data.get("department_name", "").strip()
    code = data.get("department_code", "").strip().upper()
    if not name or not code:
        return jsonify({"success": False, "error": "Name and code required."}), 400

    dept_id = Database.insert_and_get_id(
        "INSERT INTO departments (department_name, department_code) VALUES (%s, %s)",
        (name, code)
    )
    return jsonify({"success": True, "id": dept_id, "message": "Department created."})

@app.route("/api/admin/departments/<int:id>", methods=["PUT", "DELETE"])
def update_delete_department(id):
    if request.method == "DELETE":
        Database.execute("DELETE FROM departments WHERE id = %s", (id,))
        return jsonify({"success": True, "message": "Department deleted."})

    data = request.get_json() or {}
    name = data.get("department_name", "").strip()
    code = data.get("department_code", "").strip().upper()
    Database.execute(
        "UPDATE departments SET department_name = %s, department_code = %s WHERE id = %s",
        (name, code, id)
    )
    return jsonify({"success": True, "message": "Department updated."})

# 2. Faculty
@app.route("/api/admin/faculty", methods=["GET", "POST"])
def manage_faculty():
    if request.method == "GET":
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
    password = data.get("password", "faculty123").strip()
    dept_id = data.get("department_id")
    designation = data.get("designation", "Assistant Professor")

    if not name or not email or not dept_id:
        return jsonify({"success": False, "error": "Name, email, and department are required."}), 400

    u_id = Database.insert_and_get_id(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'faculty')",
        (name, email, generate_password_hash(password))
    )
    f_id = Database.insert_and_get_id(
        "INSERT INTO faculty (user_id, department_id, designation) VALUES (%s, %s, %s)",
        (u_id, dept_id, designation)
    )
    return jsonify({"success": True, "faculty_id": f_id, "message": "Faculty added."})

@app.route("/api/admin/faculty/<int:id>", methods=["DELETE"])
def delete_faculty(id):
    fac = Database.query_one("SELECT user_id FROM faculty WHERE id = %s", (id,))
    if fac:
        Database.execute("DELETE FROM users WHERE id = %s", (fac["user_id"],))
    return jsonify({"success": True, "message": "Faculty deleted."})

# 3. Students
@app.route("/api/admin/students", methods=["GET", "POST"])
def manage_students():
    if request.method == "GET":
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
    dept_id = data.get("department_id")
    semester = data.get("semester", 1)
    password = data.get("password", "student123").strip()

    if not name or not email or not reg_no or not dept_id:
        return jsonify({"success": False, "error": "Name, email, register number, and department are required."}), 400

    u_id = Database.insert_and_get_id(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'student')",
        (name, email, generate_password_hash(password))
    )
    s_id = Database.insert_and_get_id(
        "INSERT INTO students (user_id, register_number, department_id, semester) VALUES (%s, %s, %s, %s)",
        (u_id, reg_no, dept_id, semester)
    )
    return jsonify({"success": True, "student_id": s_id, "message": "Student created."})

@app.route("/api/admin/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    st = Database.query_one("SELECT user_id FROM students WHERE id = %s", (id,))
    if st:
        Database.execute("DELETE FROM users WHERE id = %s", (st["user_id"],))
    return jsonify({"success": True, "message": "Student deleted."})

# 4. Subjects
@app.route("/api/admin/subjects", methods=["GET", "POST"])
def manage_subjects():
    if request.method == "GET":
        dept_id = request.args.get("department_id")
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
        if dept_id:
            sql += " WHERE sub.department_id = %s"
            subjects = Database.query_all(sql, (dept_id,))
        else:
            subjects = Database.query_all(sql)
        return jsonify({"success": True, "subjects": subjects})

    data = request.get_json() or {}
    name = data.get("subject_name", "").strip()
    code = data.get("subject_code", "").strip().upper()
    dept_id = data.get("department_id")
    semester = data.get("semester", 1)
    credits = data.get("credits", 3)

    if not name or not code or not dept_id:
        return jsonify({"success": False, "error": "Subject name, code, and department required."}), 400

    s_id = Database.insert_and_get_id("""
        INSERT INTO subjects (subject_name, subject_code, department_id, semester, credits)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, code, dept_id, semester, credits))

    return jsonify({"success": True, "subject_id": s_id, "message": "Subject created."})

@app.route("/api/admin/subjects/<int:id>", methods=["DELETE"])
def delete_subject(id):
    Database.execute("DELETE FROM subjects WHERE id = %s", (id,))
    return jsonify({"success": True, "message": "Subject deleted."})

# 5. Audit Logs
@app.route("/api/admin/audit-logs", methods=["GET"])
def get_audit_logs():
    limit = int(request.args.get("limit", 100))
    logs = Database.query_all(f"""
        SELECT al.*,
               u.name as changed_by_name,
               u.role as changed_by_role,
               st_u.name as student_name,
               st.register_number,
               sub.subject_code,
               sub.subject_name,
               a.attendance_date
        FROM attendance_logs al
        LEFT JOIN users u ON al.changed_by = u.id
        JOIN attendance a ON al.attendance_id = a.id
        JOIN students st ON a.student_id = st.id
        JOIN users st_u ON st.user_id = st_u.id
        JOIN subjects sub ON a.subject_id = sub.id
        ORDER BY al.id DESC
        LIMIT {limit}
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
    print(f"  Backend server running at: http://127.0.0.1:{port}              ")
    print(f"==================================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
