"""
Automated Attendance Management System Using Finite Automata
Flask RESTful Backend Application & Static Asset Server
"""

import csv
import datetime
import io
import os
import sys

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

sys.path.insert(0, os.path.dirname(__file__))

from database import Database
from dfa_engine import AttendanceDFA, DFAAlphabet, DFAState

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
    static_url_path="",
)
CORS(app)

Database.init_database()
from seed_data import seed_all

seed_all()


def as_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_current_user_from_header():
    user_id = request.headers.get("X-User-Id") or request.args.get("user_id")
    parsed_id = as_id(user_id)
    return Database.find_one("users", {"id": parsed_id}) if parsed_id is not None else None


def status_from_state(state):
    return {
        DFAState.S0: "Not Marked",
        DFAState.S1: "Present",
        DFAState.S2: "Absent",
        DFAState.S3: "Late",
        DFAState.S4: "Finalized",
    }.get(state, "Not Marked")


def linked_student(student):
    if not student:
        return None
    user = Database.find_one("users", {"id": student["user_id"]}) or {}
    department = Database.find_one("departments", {"id": student["department_id"]}) or {}
    return {
        **student,
        "name": user.get("name"),
        "email": user.get("email"),
        "department_name": department.get("department_name"),
        "department_code": department.get("department_code"),
    }


def linked_faculty(faculty):
    if not faculty:
        return None
    user = Database.find_one("users", {"id": faculty["user_id"]}) or {}
    department = Database.find_one("departments", {"id": faculty["department_id"]}) or {}
    return {
        **faculty,
        "name": user.get("name"),
        "email": user.get("email"),
        "department_name": department.get("department_name"),
        "department_code": department.get("department_code"),
    }


def attendance_for(student_id, subject_id, date_string):
    return Database.find_one(
        "attendance",
        {
            "student_id": student_id,
            "subject_id": subject_id,
            "attendance_date": date_string,
        },
    )


def delete_attendance_for(query):
    for attendance in Database.find("attendance", query):
        Database.delete("attendance_logs", {"attendance_id": attendance["id"]})
    Database.delete("attendance", query)


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    user = Database.find_one("users", {"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "error": "Invalid email or password."}), 401

    extra_info = {}
    if user["role"] == "faculty":
        faculty = Database.find_one("faculty", {"user_id": user["id"]})
        if faculty:
            linked = linked_faculty(faculty)
            extra_info = {
                "faculty_id": linked["id"],
                "department_id": linked["department_id"],
                "department_name": linked["department_name"],
                "department_code": linked["department_code"],
                "designation": linked.get("designation"),
            }
    elif user["role"] == "student":
        student = Database.find_one("students", {"user_id": user["id"]})
        if student:
            linked = linked_student(student)
            extra_info = {
                "student_id": linked["id"],
                "register_number": linked["register_number"],
                "department_id": linked["department_id"],
                "department_name": linked["department_name"],
                "department_code": linked["department_code"],
                "semester": linked["semester"],
            }

    return jsonify(
        {
            "success": True,
            "token": f"token-{user['id']}-{user['role']}",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                **extra_info,
            },
        }
    )


@app.route("/api/auth/demo-users", methods=["GET"])
def get_demo_users():
    demo_emails = {
        "admin@college.edu",
        "faculty1@college.edu",
        "faculty2@college.edu",
        "student1@college.edu",
        "student8@college.edu",
    }
    demo_users = []
    for user in Database.find("users", {"email": {"$in": list(demo_emails)}}):
        department_code = ""
        if user["role"] == "faculty":
            faculty = Database.find_one("faculty", {"user_id": user["id"]})
            department = Database.find_one(
                "departments", {"id": faculty["department_id"]}
            ) if faculty else None
        elif user["role"] == "student":
            student = Database.find_one("students", {"user_id": user["id"]})
            department = Database.find_one(
                "departments", {"id": student["department_id"]}
            ) if student else None
        else:
            department = None
        if department:
            department_code = department.get("department_code", "")
        demo_users.append(
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "dept_code": department_code,
            }
        )
    demo_users.sort(key=lambda user: (user["role"], user["id"]))
    return jsonify({"success": True, "demo_users": demo_users})


@app.route("/api/dfa/info", methods=["GET"])
def get_dfa_info():
    return jsonify({"success": True, "dfa": AttendanceDFA.get_formal_definition()})


@app.route("/api/dfa/simulate", methods=["POST"])
def simulate_dfa():
    data = request.get_json() or {}
    result = AttendanceDFA.simulate_sequence(
        data.get("initial_state", DFAState.S0),
        data.get("sequence", []),
        role=data.get("role", "faculty"),
    )
    return jsonify({"success": True, "simulation": result})


@app.route("/api/attendance/sheet", methods=["GET"])
def get_attendance_sheet():
    subject_id = as_id(request.args.get("subject_id"))
    date_string = request.args.get("date")
    if subject_id is None or not date_string:
        return jsonify({"success": False, "error": "subject_id and date are required."}), 400

    subject = Database.find_one("subjects", {"id": subject_id})
    if not subject:
        return jsonify({"success": False, "error": "Subject not found."}), 404

    students = []
    enrollments = Database.find("enrollments", {"subject_id": subject_id})
    for enrollment in enrollments:
        student = Database.find_one("students", {"id": enrollment["student_id"]})
        linked = linked_student(student)
        if not linked:
            continue
        attendance = attendance_for(linked["id"], subject_id, date_string)
        students.append(
            {
                "student_id": linked["id"],
                "register_number": linked["register_number"],
                "semester": linked["semester"],
                "name": linked["name"],
                "email": linked["email"],
                "attendance_id": attendance.get("id") if attendance else None,
                "automata_state": attendance.get("automata_state", "S0") if attendance else "S0",
                "status": attendance.get("status", "Not Marked") if attendance else "Not Marked",
                "marked_by": attendance.get("marked_by") if attendance else None,
                "updated_at": attendance.get("updated_at") if attendance else None,
            }
        )
    students.sort(key=lambda student: student["register_number"])
    is_finalized = any(student["automata_state"] == DFAState.S4 for student in students)

    for student in students:
        valid_actions = []
        for symbol, name in DFAAlphabet.DESCRIPTIONS.items():
            transition = AttendanceDFA.validate_transition(
                student["automata_state"], symbol, user_role="faculty"
            )
            if transition.valid:
                valid_actions.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "target_state": transition.next_state,
                        "target_state_name": DFAState.NAMES.get(transition.next_state, ""),
                    }
                )
        student["allowed_transitions"] = valid_actions

    return jsonify(
        {
            "success": True,
            "subject": subject,
            "date": date_string,
            "is_finalized": is_finalized,
            "students": students,
            "total_enrolled": len(students),
        }
    )


@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    data = request.get_json() or {}
    student_id = as_id(data.get("student_id"))
    subject_id = as_id(data.get("subject_id"))
    date_string = data.get("date")
    symbol = data.get("symbol")
    reason = data.get("reason", "").strip()
    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    if student_id is None or subject_id is None or not date_string or not symbol:
        return jsonify(
            {
                "success": False,
                "error": "student_id, subject_id, date, and symbol are required.",
            }
        ), 400

    existing = attendance_for(student_id, subject_id, date_string)
    current_state = existing["automata_state"] if existing else DFAState.S0
    transition = AttendanceDFA.validate_transition(
        current_state=current_state,
        input_symbol=symbol,
        user_role=user_role,
        has_audit_reason=bool(reason),
    )
    if not transition.valid:
        return jsonify(
            {
                "success": False,
                "error_type": "DFA_TRANSITION_REJECTED",
                "error": transition.message,
                "current_state": current_state,
                "attempted_symbol": symbol,
                "details": transition.details,
            }
        ), 400

    next_state = transition.next_state
    status = status_from_state(next_state)
    values = {
        "status": status,
        "automata_state": next_state,
        "marked_by": user_id,
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if existing:
        attendance_id = existing["id"]
        Database.update("attendance", {"id": attendance_id}, values)
    else:
        attendance_id = Database.insert(
            "attendance",
            {
                "student_id": student_id,
                "subject_id": subject_id,
                "attendance_date": date_string,
                **values,
            },
        )

    Database.insert(
        "attendance_logs",
        {
            "attendance_id": attendance_id,
            "previous_state": current_state,
            "input_symbol": symbol,
            "next_state": next_state,
            "changed_by": user_id,
            "reason": reason or transition.details.get(
                "description", f"Transitioned to {next_state}"
            ),
        },
    )
    return jsonify(
        {
            "success": True,
            "message": transition.message,
            "attendance_id": attendance_id,
            "previous_state": current_state,
            "next_state": next_state,
            "status": status,
            "dfa_details": transition.to_dict(),
        }
    )


@app.route("/api/attendance/batch", methods=["POST"])
def batch_mark_attendance():
    data = request.get_json() or {}
    subject_id = as_id(data.get("subject_id"))
    date_string = data.get("date")
    symbol = data.get("symbol", "P")
    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None
    enrollments = Database.find("enrollments", {"subject_id": subject_id})
    if not enrollments:
        return jsonify(
            {"success": False, "error": "No students enrolled in this subject."}
        ), 400

    updated_count = 0
    rejected_count = 0
    errors = []
    for enrollment in enrollments:
        student_id = enrollment["student_id"]
        existing = attendance_for(student_id, subject_id, date_string)
        current_state = existing["automata_state"] if existing else DFAState.S0
        transition = AttendanceDFA.validate_transition(
            current_state, symbol, user_role=user_role
        )
        if not transition.valid:
            rejected_count += 1
            errors.append(f"Student ID {student_id}: {transition.message}")
            continue

        next_state = transition.next_state
        values = {
            "status": status_from_state(next_state),
            "automata_state": next_state,
            "marked_by": user_id,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if existing:
            attendance_id = existing["id"]
            Database.update("attendance", {"id": attendance_id}, values)
        else:
            attendance_id = Database.insert(
                "attendance",
                {
                    "student_id": student_id,
                    "subject_id": subject_id,
                    "attendance_date": date_string,
                    **values,
                },
            )
        Database.insert(
            "attendance_logs",
            {
                "attendance_id": attendance_id,
                "previous_state": current_state,
                "input_symbol": symbol,
                "next_state": next_state,
                "changed_by": user_id,
                "reason": f"Batch transition: {symbol}",
            },
        )
        updated_count += 1

    return jsonify(
        {
            "success": True,
            "updated_count": updated_count,
            "rejected_count": rejected_count,
            "errors": errors,
        }
    )


@app.route("/api/attendance/finalize", methods=["POST"])
def finalize_session():
    data = request.get_json() or {}
    subject_id = as_id(data.get("subject_id"))
    date_string = data.get("date")
    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "faculty"
    user_id = current_user["id"] if current_user else None

    students = []
    for enrollment in Database.find("enrollments", {"subject_id": subject_id}):
        student_id = enrollment["student_id"]
        attendance = attendance_for(student_id, subject_id, date_string)
        students.append(
            {
                "student_id": student_id,
                "attendance_id": attendance["id"] if attendance else 0,
                "automata_state": (
                    attendance["automata_state"] if attendance else DFAState.S0
                ),
            }
        )
    if not students:
        return jsonify(
            {"success": False, "error": "No students found for this subject."}
        ), 400

    unmarked = [student for student in students if student["automata_state"] == DFAState.S0]
    if unmarked:
        return jsonify(
            {
                "success": False,
                "error_type": "DFA_FINALIZATION_REJECTED",
                "error": (
                    f"Cannot finalize attendance: {len(unmarked)} student(s) are still "
                    "in state S0 (Not Marked). DFA transition δ(S0, F) is undefined. "
                    "Please mark all students before finalization."
                ),
            }
        ), 400

    finalized_count = 0
    for student in students:
        current_state = student["automata_state"]
        if current_state == DFAState.S4:
            continue
        transition = AttendanceDFA.validate_transition(
            current_state, DFAAlphabet.F, user_role=user_role
        )
        if transition.valid:
            attendance_id = student["attendance_id"]
            Database.update(
                "attendance",
                {"id": attendance_id},
                {
                    "status": "Finalized",
                    "automata_state": DFAState.S4,
                    "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            Database.insert(
                "attendance_logs",
                {
                    "attendance_id": attendance_id,
                    "previous_state": current_state,
                    "input_symbol": DFAAlphabet.F,
                    "next_state": DFAState.S4,
                    "changed_by": user_id,
                    "reason": "Session Finalized via DFA input F",
                },
            )
            finalized_count += 1

    return jsonify(
        {
            "success": True,
            "message": (
                f"Successfully finalized {finalized_count} attendance records. "
                "All records are now locked in DFA state S4."
            ),
            "finalized_count": finalized_count,
        }
    )


@app.route("/api/attendance/reset", methods=["POST"])
def admin_reset_attendance():
    data = request.get_json() or {}
    attendance_id = as_id(data.get("attendance_id"))
    reason = data.get("reason", "").strip()
    current_user = get_current_user_from_header()
    user_role = current_user["role"] if current_user else "student"
    user_id = current_user["id"] if current_user else None
    if user_role != "admin":
        return jsonify(
            {
                "success": False,
                "error_type": "UNAUTHORIZED_DFA_RESET",
                "error": (
                    "Access Denied: Only administrators have authorization to execute "
                    "DFA transition δ(S4, R) -> S0."
                ),
            }
        ), 403
    if not reason:
        return jsonify(
            {
                "success": False,
                "error_type": "MISSING_AUDIT_REASON",
                "error": "An audit explanation is strictly mandatory when resetting finalized attendance records.",
            }
        ), 400

    attendance = Database.find_one("attendance", {"id": attendance_id})
    if not attendance:
        return jsonify({"success": False, "error": "Attendance record not found."}), 404
    current_state = attendance["automata_state"]
    transition = AttendanceDFA.validate_transition(
        current_state, DFAAlphabet.R, user_role="admin", has_audit_reason=True
    )
    if not transition.valid:
        return jsonify({"success": False, "error": transition.message}), 400

    Database.update(
        "attendance",
        {"id": attendance_id},
        {
            "status": "Not Marked",
            "automata_state": DFAState.S0,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    Database.insert(
        "attendance_logs",
        {
            "attendance_id": attendance_id,
            "previous_state": current_state,
            "input_symbol": DFAAlphabet.R,
            "next_state": DFAState.S0,
            "changed_by": user_id,
            "reason": f"Admin Reset: {reason}",
        },
    )
    return jsonify(
        {
            "success": True,
            "message": f"Authorized Admin Reset complete: Transitioned {current_state} -> S0.",
            "previous_state": current_state,
            "next_state": "S0",
        }
    )


def build_reports():
    department_id = as_id(request.args.get("department_id"))
    semester = as_id(request.args.get("semester"))
    subject_filter = as_id(request.args.get("subject_id"))
    student_filter = as_id(request.args.get("student_id"))
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    reports = []

    for enrollment in Database.find("enrollments"):
        student = Database.find_one("students", {"id": enrollment["student_id"]})
        subject = Database.find_one("subjects", {"id": enrollment["subject_id"]})
        if not student or not subject:
            continue
        department = Database.find_one(
            "departments", {"id": student["department_id"]}
        )
        user = Database.find_one("users", {"id": student["user_id"]})
        if not department or not user:
            continue
        if department_id is not None and student["department_id"] != department_id:
            continue
        if semester is not None and student["semester"] != semester:
            continue
        if subject_filter is not None and subject["id"] != subject_filter:
            continue
        if student_filter is not None and student["id"] != student_filter:
            continue

        records = Database.find(
            "attendance",
            {
                "student_id": student["id"],
                "subject_id": subject["id"],
            },
        )
        if from_date:
            records = [
                record for record in records
                if str(record["attendance_date"]) >= from_date
            ]
        if to_date:
            records = [
                record for record in records
                if str(record["attendance_date"]) <= to_date
            ]

        present = absent = late = 0
        for record in records:
            status = record["status"]
            if status == "Finalized":
                first_mark = next(
                    (
                        log["input_symbol"]
                        for log in sorted(
                            Database.find(
                                "attendance_logs",
                                {"attendance_id": record["id"]},
                                sort=[("id", 1)],
                            ),
                            key=lambda log: log["id"],
                        )
                        if log["input_symbol"] in {"P", "A", "L"}
                    ),
                    "P",
                )
                status = {"P": "Present", "A": "Absent", "L": "Late"}[first_mark]
            if status == "Present":
                present += 1
            elif status == "Absent":
                absent += 1
            elif status == "Late":
                late += 1

        total = len(records)
        percentage = round((present / total) * 100, 1) if total else 0.0
        reports.append(
            {
                "student_id": student["id"],
                "register_number": student["register_number"],
                "student_name": user["name"],
                "department_code": department["department_code"],
                "department_name": department["department_name"],
                "semester": student["semester"],
                "subject_id": subject["id"],
                "subject_code": subject["subject_code"],
                "subject_name": subject["subject_name"],
                "total_conducted": total,
                "present_count": present,
                "absent_count": absent,
                "late_count": late,
                "attendance_percentage": percentage,
                "below_threshold": percentage < 75.0 and total > 0,
            }
        )
    reports.sort(
        key=lambda item: (
            item["department_code"],
            item["register_number"],
            item["subject_code"],
        )
    )
    return reports


@app.route("/api/attendance/reports", methods=["GET"])
def get_attendance_reports():
    reports = build_reports()
    return jsonify({"success": True, "reports": reports, "count": len(reports)})


@app.route("/api/attendance/export-csv", methods=["GET"])
def export_attendance_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Register Number", "Student Name", "Department", "Semester",
            "Subject Code", "Subject Name", "Conducted Classes",
            "Present", "Absent", "Late", "Attendance %", "Warning (< 75%)",
        ]
    )
    for report in build_reports():
        writer.writerow(
            [
                report["register_number"],
                report["student_name"],
                report["department_code"],
                report["semester"],
                report["subject_code"],
                report["subject_name"],
                report["total_conducted"],
                report["present_count"],
                report["absent_count"],
                report["late_count"],
                f"{report['attendance_percentage']}%",
                "CRITICAL WARNING" if report["below_threshold"] else "Satisfactory",
            ]
        )
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_report.csv"},
    )


@app.route("/api/dashboard/admin", methods=["GET"])
def admin_dashboard():
    counts = {
        "students": Database.count("students"),
        "faculty": Database.count("faculty"),
        "departments": Database.count("departments"),
        "subjects": Database.count("subjects"),
        "attendance_records": Database.count("attendance"),
    }

    department_stats = []
    for department in Database.find("departments"):
        students = Database.find("students", {"department_id": department["id"]})
        student_ids = {student["id"] for student in students}
        attendance = [
            record
            for record in Database.find("attendance")
            if record["student_id"] in student_ids
        ]
        total = len(attendance)
        present = sum(record["status"] == "Present" for record in attendance)
        department_stats.append(
            {
                "department_name": department["department_name"],
                "department_code": department["department_code"],
                "total_records": total,
                "present_count": present,
                "percentage": round((present / total) * 100, 1) if total else 0.0,
            }
        )

    recent_logs = []
    for log in Database.find("attendance_logs", sort=[("id", -1)], limit=10):
        attendance = Database.find_one("attendance", {"id": log["attendance_id"]})
        if not attendance:
            continue
        student = Database.find_one("students", {"id": attendance["student_id"]})
        subject = Database.find_one("subjects", {"id": attendance["subject_id"]})
        student_user = Database.find_one(
            "users", {"id": student["user_id"]}
        ) if student else None
        changed_by = Database.find_one("users", {"id": log["changed_by"]}) if log.get("changed_by") else None
        if not student or not subject or not student_user:
            continue
        recent_logs.append(
            {
                "id": log["id"],
                "previous_state": log["previous_state"],
                "input_symbol": log["input_symbol"],
                "next_state": log["next_state"],
                "reason": log.get("reason"),
                "timestamp": log.get("timestamp"),
                "changed_by_name": changed_by.get("name") if changed_by else None,
                "student_name": student_user["name"],
                "register_number": student["register_number"],
                "subject_code": subject["subject_code"],
            }
        )

    state_counts = {}
    for record in Database.find("attendance"):
        state_counts[record["automata_state"]] = (
            state_counts.get(record["automata_state"], 0) + 1
        )
    state_distribution = [
        {"automata_state": state, "count": count}
        for state, count in sorted(state_counts.items())
    ]
    return jsonify(
        {
            "success": True,
            "counts": counts,
            "department_stats": department_stats,
            "state_distribution": state_distribution,
            "recent_logs": recent_logs,
        }
    )


@app.route("/api/dashboard/faculty", methods=["GET"])
def faculty_dashboard():
    user = get_current_user_from_header()
    user_id = user["id"] if user else as_id(request.args.get("user_id"))
    faculty = Database.find_one("faculty", {"user_id": user_id})
    if not faculty:
        return jsonify({"success": False, "error": "Faculty record not found."}), 404

    today = datetime.date.today().strftime("%Y-%m-%d")
    subjects = []
    for assignment in Database.find("faculty_subjects", {"faculty_id": faculty["id"]}):
        subject = Database.find_one("subjects", {"id": assignment["subject_id"]})
        if not subject:
            continue
        department = Database.find_one(
            "departments", {"id": subject["department_id"]}
        )
        attendance_today = Database.find(
            "attendance",
            {"subject_id": subject["id"], "attendance_date": today},
        )
        enrollments = Database.find("enrollments", {"subject_id": subject["id"]})
        subjects.append(
            {
                "id": subject["id"],
                "subject_name": subject["subject_name"],
                "subject_code": subject["subject_code"],
                "semester": subject["semester"],
                "credits": subject["credits"],
                "department_code": department.get("department_code") if department else None,
                "enrolled_students": len(enrollments),
                "today_marked_count": len(attendance_today),
                "today_state": attendance_today[0]["automata_state"] if attendance_today else None,
            }
        )
    return jsonify({"success": True, "today": today, "subjects": subjects})


@app.route("/api/dashboard/student", methods=["GET"])
def student_dashboard():
    user = get_current_user_from_header()
    user_id = user["id"] if user else as_id(request.args.get("user_id"))
    student = Database.find_one("students", {"user_id": user_id})
    profile = linked_student(student)
    if not profile:
        return jsonify({"success": False, "error": "Student record not found."}), 404

    student_id = profile["id"]
    subjects_list = []
    total_classes = total_present = total_absent = total_late = 0
    for enrollment in Database.find("enrollments", {"student_id": student_id}):
        subject = Database.find_one("subjects", {"id": enrollment["subject_id"]})
        if not subject:
            continue
        records = Database.find(
            "attendance",
            {"student_id": student_id, "subject_id": subject["id"]},
        )
        total = len(records)
        present = sum(
            record["status"] == "Present"
            or (
                record["automata_state"] == "S4"
                and record["status"] == "Finalized"
            )
            for record in records
        )
        absent = sum(record["status"] == "Absent" for record in records)
        late = sum(record["status"] == "Late" for record in records)
        percentage = round((present / total) * 100, 1) if total else 0.0
        total_classes += total
        total_present += present
        total_absent += absent
        total_late += late
        subjects_list.append(
            {
                "subject_id": subject["id"],
                "subject_name": subject["subject_name"],
                "subject_code": subject["subject_code"],
                "semester": subject["semester"],
                "total_conducted": total,
                "present_count": present,
                "absent_count": absent,
                "late_count": late,
                "percentage": percentage,
                "warning": percentage < 75.0 and total > 0,
            }
        )

    monthly = {}
    for record in Database.find("attendance", {"student_id": student_id}):
        month = str(record["attendance_date"])[:7]
        aggregate = monthly.setdefault(month, {"month": month, "total": 0, "present": 0})
        aggregate["total"] += 1
        if record["status"] == "Present" or record["automata_state"] == "S4":
            aggregate["present"] += 1

    overall_percentage = (
        round((total_present / total_classes) * 100, 1) if total_classes else 0.0
    )
    return jsonify(
        {
            "success": True,
            "profile": {
                "student_id": student_id,
                "register_number": profile["register_number"],
                "semester": profile["semester"],
                "department_name": profile["department_name"],
                "department_code": profile["department_code"],
                "name": profile["name"],
                "email": profile["email"],
            },
            "summary": {
                "overall_percentage": overall_percentage,
                "total_conducted": total_classes,
                "present": total_present,
                "absent": total_absent,
                "late": total_late,
                "warning": overall_percentage < 75.0 and total_classes > 0,
            },
            "subjects": subjects_list,
            "monthly_trend": [monthly[key] for key in sorted(monthly)],
        }
    )


@app.route("/api/admin/departments", methods=["GET", "POST"])
def manage_departments():
    if request.method == "GET":
        departments = Database.find("departments", sort=[("department_name", 1)])
        return jsonify({"success": True, "departments": departments})
    data = request.get_json() or {}
    name = data.get("department_name", "").strip()
    code = data.get("department_code", "").strip().upper()
    if not name or not code:
        return jsonify({"success": False, "error": "Name and code required."}), 400
    department_id = Database.insert(
        "departments", {"department_name": name, "department_code": code}
    )
    return jsonify({"success": True, "id": department_id, "message": "Department created."})


@app.route("/api/admin/departments/<int:id>", methods=["PUT", "DELETE"])
def update_delete_department(id):
    if request.method == "DELETE":
        faculty = Database.find("faculty", {"department_id": id})
        for member in faculty:
            Database.delete("faculty_subjects", {"faculty_id": member["id"]})
            Database.delete("users", {"id": member["user_id"]})
        students = Database.find("students", {"department_id": id})
        for student in students:
            Database.delete("enrollments", {"student_id": student["id"]})
            delete_attendance_for({"student_id": student["id"]})
            Database.delete("users", {"id": student["user_id"]})
        subjects = Database.find("subjects", {"department_id": id})
        for subject in subjects:
            Database.delete("faculty_subjects", {"subject_id": subject["id"]})
            Database.delete("enrollments", {"subject_id": subject["id"]})
            delete_attendance_for({"subject_id": subject["id"]})
        Database.delete("faculty", {"department_id": id})
        Database.delete("students", {"department_id": id})
        Database.delete("subjects", {"department_id": id})
        Database.delete("departments", {"id": id})
        return jsonify({"success": True, "message": "Department deleted."})
    data = request.get_json() or {}
    Database.update(
        "departments",
        {"id": id},
        {
            "department_name": data.get("department_name", "").strip(),
            "department_code": data.get("department_code", "").strip().upper(),
        },
    )
    return jsonify({"success": True, "message": "Department updated."})


@app.route("/api/admin/faculty", methods=["GET", "POST"])
def manage_faculty():
    if request.method == "GET":
        faculty_rows = []
        for faculty in Database.find("faculty"):
            linked = linked_faculty(faculty)
            if not linked or not linked.get("name"):
                continue
            faculty_rows.append(
                {
                    "id": faculty["id"],
                    "user_id": faculty["user_id"],
                    "name": linked["name"],
                    "email": linked["email"],
                    "designation": faculty.get("designation"),
                    "department_id": faculty["department_id"],
                    "department_name": linked["department_name"],
                    "department_code": linked["department_code"],
                    "subjects_count": Database.count(
                        "faculty_subjects", {"faculty_id": faculty["id"]}
                    ),
                }
            )
        faculty_rows.sort(key=lambda member: member["name"])
        return jsonify({"success": True, "faculty": faculty_rows})

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "faculty123").strip()
    department_id = as_id(data.get("department_id"))
    designation = data.get("designation", "Assistant Professor")
    if not name or not email or department_id is None:
        return jsonify(
            {"success": False, "error": "Name, email, and department are required."}
        ), 400
    user_id = Database.insert(
        "users",
        {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "role": "faculty",
        },
    )
    faculty_id = Database.insert(
        "faculty",
        {
            "user_id": user_id,
            "department_id": department_id,
            "designation": designation,
        },
    )
    return jsonify({"success": True, "faculty_id": faculty_id, "message": "Faculty added."})


@app.route("/api/admin/faculty/<int:id>", methods=["DELETE"])
def delete_faculty(id):
    faculty = Database.find_one("faculty", {"id": id})
    if faculty:
        Database.delete("faculty_subjects", {"faculty_id": id})
        Database.delete("faculty", {"id": id})
        Database.delete("users", {"id": faculty["user_id"]})
    return jsonify({"success": True, "message": "Faculty deleted."})


@app.route("/api/admin/students", methods=["GET", "POST"])
def manage_students():
    if request.method == "GET":
        student_rows = []
        for student in Database.find("students"):
            linked = linked_student(student)
            if not linked or not linked.get("name"):
                continue
            student_rows.append(
                {
                    "id": student["id"],
                    "user_id": student["user_id"],
                    "register_number": student["register_number"],
                    "semester": student["semester"],
                    "name": linked["name"],
                    "email": linked["email"],
                    "department_name": linked["department_name"],
                    "department_code": linked["department_code"],
                    "department_id": student["department_id"],
                    "enrolled_subjects": Database.count(
                        "enrollments", {"student_id": student["id"]}
                    ),
                }
            )
        student_rows.sort(key=lambda row: row["register_number"])
        return jsonify({"success": True, "students": student_rows})

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    register_number = data.get("register_number", "").strip().upper()
    department_id = as_id(data.get("department_id"))
    semester = data.get("semester", 1)
    password = data.get("password", "student123").strip()
    if not name or not email or not register_number or department_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Name, email, register number, and department are required.",
            }
        ), 400
    user_id = Database.insert(
        "users",
        {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "role": "student",
        },
    )
    student_id = Database.insert(
        "students",
        {
            "user_id": user_id,
            "register_number": register_number,
            "department_id": department_id,
            "semester": semester,
        },
    )
    return jsonify({"success": True, "student_id": student_id, "message": "Student created."})


@app.route("/api/admin/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    student = Database.find_one("students", {"id": id})
    if student:
        Database.delete("enrollments", {"student_id": id})
        delete_attendance_for({"student_id": id})
        Database.delete("students", {"id": id})
        Database.delete("users", {"id": student["user_id"]})
    return jsonify({"success": True, "message": "Student deleted."})


@app.route("/api/admin/subjects", methods=["GET", "POST"])
def manage_subjects():
    if request.method == "GET":
        department_id = as_id(request.args.get("department_id"))
        subjects = []
        for subject in Database.find("subjects"):
            if department_id is not None and subject["department_id"] != department_id:
                continue
            department = Database.find_one(
                "departments", {"id": subject["department_id"]}
            )
            if not department:
                continue
            assignment = Database.find_one("faculty_subjects", {"subject_id": subject["id"]})
            assigned_faculty_name = None
            if assignment:
                faculty = Database.find_one("faculty", {"id": assignment["faculty_id"]})
                user = Database.find_one(
                    "users", {"id": faculty["user_id"]}
                ) if faculty else None
                assigned_faculty_name = user.get("name") if user else None
            subjects.append(
                {
                    **subject,
                    "department_name": department["department_name"],
                    "department_code": department["department_code"],
                    "enrolled_students": Database.count(
                        "enrollments", {"subject_id": subject["id"]}
                    ),
                    "assigned_faculty_name": assigned_faculty_name,
                }
            )
        return jsonify({"success": True, "subjects": subjects})

    data = request.get_json() or {}
    name = data.get("subject_name", "").strip()
    code = data.get("subject_code", "").strip().upper()
    department_id = as_id(data.get("department_id"))
    semester = data.get("semester", 1)
    credits = data.get("credits", 3)
    if not name or not code or department_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Subject name, code, and department required.",
            }
        ), 400
    subject_id = Database.insert(
        "subjects",
        {
            "subject_name": name,
            "subject_code": code,
            "department_id": department_id,
            "semester": semester,
            "credits": credits,
        },
    )
    return jsonify({"success": True, "subject_id": subject_id, "message": "Subject created."})


@app.route("/api/admin/subjects/<int:id>", methods=["DELETE"])
def delete_subject(id):
    Database.delete("faculty_subjects", {"subject_id": id})
    Database.delete("enrollments", {"subject_id": id})
    delete_attendance_for({"subject_id": id})
    Database.delete("subjects", {"id": id})
    return jsonify({"success": True, "message": "Subject deleted."})


@app.route("/api/admin/audit-logs", methods=["GET"])
def get_audit_logs():
    limit = max(0, min(as_id(request.args.get("limit", 100)) or 100, 1000))
    logs = []
    for log in Database.find("attendance_logs", sort=[("id", -1)], limit=limit):
        attendance = Database.find_one("attendance", {"id": log["attendance_id"]})
        if not attendance:
            continue
        student = Database.find_one("students", {"id": attendance["student_id"]})
        subject = Database.find_one("subjects", {"id": attendance["subject_id"]})
        student_user = Database.find_one(
            "users", {"id": student["user_id"]}
        ) if student else None
        changed_by = Database.find_one(
            "users", {"id": log["changed_by"]}
        ) if log.get("changed_by") is not None else None
        if not student or not subject or not student_user:
            continue
        logs.append(
            {
                **log,
                "changed_by_name": changed_by.get("name") if changed_by else None,
                "changed_by_role": changed_by.get("role") if changed_by else None,
                "student_name": student_user["name"],
                "register_number": student["register_number"],
                "subject_code": subject["subject_code"],
                "subject_name": subject["subject_name"],
                "attendance_date": attendance["attendance_date"],
            }
        )
    return jsonify({"success": True, "logs": logs, "count": len(logs)})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    static_folder = app.static_folder
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    return send_from_directory(static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("==================================================================")
    print("  AUTOMATED ATTENDANCE MANAGEMENT SYSTEM USING FINITE AUTOMATA    ")
    print(f"  Backend server running at: http://127.0.0.1:{port}              ")
    print("==================================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
