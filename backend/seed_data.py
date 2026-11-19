"""
Dual Database Seeder (MongoDB and SQLite)
Populates:
- 3 Departments (CSE, ECE, IT)
- 1 Admin
- 5 Faculty Members
- 6 Subjects & Faculty Assignments
- 30 Students & Subject Enrollments
- Historical Attendance Records with Finite Automata (DFA) Audit Logs
"""

import datetime
from werkzeug.security import generate_password_hash
from database import Database
from mongo_db import MongoDB

def seed_mongo():
    db = MongoDB.get_db()
    if db is None:
        return

    print("[SEED MONGODB] Checking if MongoDB collections need seeding...")
    if db.users.count_documents({}) > 0:
        print("[SEED MONGODB] MongoDB already seeded. Skipping.")
        return

    print("[SEED MONGODB] Seeding collections...")

    # 1. Departments
    dept_docs = [
        {"id": 1, "department_name": "Computer Science & Engineering", "department_code": "CSE", "created_at": datetime.datetime.utcnow()},
        {"id": 2, "department_name": "Electronics & Communication Engineering", "department_code": "ECE", "created_at": datetime.datetime.utcnow()},
        {"id": 3, "department_name": "Information Technology", "department_code": "IT", "created_at": datetime.datetime.utcnow()}
    ]
    db.departments.insert_many(dept_docs)
    db.counters.update_one({"_id": "departments"}, {"$set": {"seq": 3}}, upsert=True)

    # 2. Admin User
    admin_pw = generate_password_hash("admin123")
    admin_doc = {
        "id": 1,
        "name": "Dr. Alan Turing (System Administrator)",
        "email": "admin@college.edu",
        "password": admin_pw,
        "role": "admin",
        "created_at": datetime.datetime.utcnow()
    }
    db.users.insert_one(admin_doc)

    # 3. Faculty Users
    faculty_list = [
        ("Prof. Grace Hopper", "faculty1@college.edu", 1, "Professor & HOD"),
        ("Prof. John von Neumann", "faculty2@college.edu", 1, "Associate Professor"),
        ("Prof. Claude Shannon", "faculty3@college.edu", 2, "Professor"),
        ("Prof. Ada Lovelace", "faculty4@college.edu", 3, "Associate Professor"),
        ("Prof. Donald Knuth", "faculty5@college.edu", 3, "Assistant Professor")
    ]
    fac_pw = generate_password_hash("faculty123")
    fac_users = []
    fac_docs = []
    for idx, (name, email, dept_id, desig) in enumerate(faculty_list, start=2):
        fac_users.append({
            "id": idx,
            "name": name,
            "email": email,
            "password": fac_pw,
            "role": "faculty",
            "created_at": datetime.datetime.utcnow()
        })
        fac_docs.append({
            "id": idx - 1,
            "user_id": idx,
            "department_id": dept_id,
            "designation": desig,
            "created_at": datetime.datetime.utcnow()
        })
    db.users.insert_many(fac_users)
    db.faculty.insert_many(fac_docs)
    db.counters.update_one({"_id": "faculty"}, {"$set": {"seq": len(fac_docs)}}, upsert=True)

    # 4. Subjects
    subj_list = [
        (1, "Theory of Computation & Automata", "CS301", 1, 5, 4),
        (2, "Database Management Systems", "CS302", 1, 5, 3),
        (3, "Digital Signal Processing", "EC301", 2, 5, 4),
        (4, "Microprocessors & Microcontrollers", "EC302", 2, 5, 3),
        (5, "Web Technologies & Frameworks", "IT301", 3, 5, 4),
        (6, "Cloud Computing Architecture", "IT302", 3, 5, 3)
    ]
    subj_docs = [
        {"id": s_id, "subject_name": s_name, "subject_code": s_code, "department_id": d_id, "semester": sem, "credits": cred, "created_at": datetime.datetime.utcnow()}
        for s_id, s_name, s_code, d_id, sem, cred in subj_list
    ]
    db.subjects.insert_many(subj_docs)
    db.counters.update_one({"_id": "subjects"}, {"$set": {"seq": 6}}, upsert=True)

    # 5. Faculty Subject Assignments
    fac_subj = [
        {"id": 1, "faculty_id": 1, "subject_id": 1, "assigned_at": datetime.datetime.utcnow()},
        {"id": 2, "faculty_id": 2, "subject_id": 2, "assigned_at": datetime.datetime.utcnow()},
        {"id": 3, "faculty_id": 3, "subject_id": 3, "assigned_at": datetime.datetime.utcnow()},
        {"id": 4, "faculty_id": 3, "subject_id": 4, "assigned_at": datetime.datetime.utcnow()},
        {"id": 5, "faculty_id": 4, "subject_id": 5, "assigned_at": datetime.datetime.utcnow()},
        {"id": 6, "faculty_id": 5, "subject_id": 6, "assigned_at": datetime.datetime.utcnow()}
    ]
    db.faculty_subjects.insert_many(fac_subj)

    # 6. 30 Students
    student_names = [
        ("Alice Walker", "student1@college.edu", "2024CSE001", 1, 5),
        ("Bob Miller", "student2@college.edu", "2024CSE002", 1, 5),
        ("Charlie Davis", "student3@college.edu", "2024CSE003", 1, 5),
        ("Diana Prince", "student4@college.edu", "2024CSE004", 1, 5),
        ("Ethan Hunt", "student5@college.edu", "2024CSE005", 1, 5),
        ("Fiona Gallagher", "student6@college.edu", "2024CSE006", 1, 5),
        ("George Clark", "student7@college.edu", "2024CSE007", 1, 5),
        ("Hannah Abbott", "student8@college.edu", "2024CSE008", 1, 5),
        ("Ian Wright", "student9@college.edu", "2024CSE009", 1, 5),
        ("Julia Roberts", "student10@college.edu", "2024CSE010", 1, 5),

        ("Kevin Peterson", "student11@college.edu", "2024ECE001", 2, 5),
        ("Laura Croft", "student12@college.edu", "2024ECE002", 2, 5),
        ("Michael Scott", "student13@college.edu", "2024ECE003", 2, 5),
        ("Nancy Wheeler", "student14@college.edu", "2024ECE004", 2, 5),
        ("Oliver Queen", "student15@college.edu", "2024ECE005", 2, 5),
        ("Peter Parker", "student16@college.edu", "2024ECE006", 2, 5),
        ("Quinn Fabray", "student17@college.edu", "2024ECE007", 2, 5),
        ("Rachel Green", "student18@college.edu", "2024ECE008", 2, 5),
        ("Steve Rogers", "student19@college.edu", "2024ECE009", 2, 5),
        ("Tony Stark", "student20@college.edu", "2024ECE010", 2, 5),

        ("Uma Thurman", "student21@college.edu", "2024IT001", 3, 5),
        ("Victor Stone", "student22@college.edu", "2024IT002", 3, 5),
        ("Wanda Maximoff", "student23@college.edu", "2024IT003", 3, 5),
        ("Xavier Thorne", "student24@college.edu", "2024IT004", 3, 5),
        ("Yara Greyjoy", "student25@college.edu", "2024IT005", 3, 5),
        ("Zack Snyder", "student26@college.edu", "2024IT006", 3, 5),
        ("Arthur Dent", "student27@college.edu", "2024IT007", 3, 5),
        ("Beth Harmon", "student28@college.edu", "2024IT008", 3, 5),
        ("Cedric Diggory", "student29@college.edu", "2024IT009", 3, 5),
        ("Daisy Johnson", "student30@college.edu", "2024IT010", 3, 5)
    ]
    stud_pw = generate_password_hash("student123")
    stud_users = []
    stud_docs = []
    enroll_docs = []

    start_u_id = 7
    enroll_id = 1
    for s_idx, (s_name, s_email, s_reg, s_dept, s_sem) in enumerate(student_names, start=1):
        u_id = start_u_id + s_idx - 1
        stud_users.append({
            "id": u_id,
            "name": s_name,
            "email": s_email,
            "password": stud_pw,
            "role": "student",
            "created_at": datetime.datetime.utcnow()
        })
        stud_docs.append({
            "id": s_idx,
            "user_id": u_id,
            "register_number": s_reg,
            "department_id": s_dept,
            "semester": s_sem,
            "created_at": datetime.datetime.utcnow()
        })

        # Enrollments
        dept_subjs = [1, 2] if s_dept == 1 else ([3, 4] if s_dept == 2 else [5, 6])
        for sub_id in dept_subjs:
            enroll_docs.append({
                "id": enroll_id,
                "student_id": s_idx,
                "subject_id": sub_id,
                "enrolled_at": datetime.datetime.utcnow()
            })
            enroll_id += 1

    db.users.insert_many(stud_users)
    db.students.insert_many(stud_docs)
    db.enrollments.insert_many(enroll_docs)
    db.counters.update_one({"_id": "users"}, {"$set": {"seq": start_u_id + len(student_names) - 1}}, upsert=True)
    db.counters.update_one({"_id": "students"}, {"$set": {"seq": 30}}, upsert=True)
    db.counters.update_one({"_id": "enrollments"}, {"$set": {"seq": len(enroll_docs)}}, upsert=True)

    # 7. Attendance Records & DFA Logs
    today = datetime.date.today()
    past_dates = [today - datetime.timedelta(days=i) for i in range(1, 8)]
    att_docs = []
    log_docs = []
    att_id = 1
    log_id = 1

    for d_idx, att_date in enumerate(past_dates):
        date_str = att_date.strftime("%Y-%m-%d")
        is_finalized = (d_idx > 0)

        for s_idx in range(1, 11): # CSE students
            if s_idx == 8: # Hannah Abbott (Warning student)
                status_choice = "Absent" if (d_idx % 2 == 0) else "Late"
                state_choice = "S2" if status_choice == "Absent" else "S3"
                symbol = "A" if status_choice == "Absent" else "L"
            else:
                if (s_idx + d_idx) % 7 == 0:
                    status_choice = "Absent"
                    state_choice = "S2"
                    symbol = "A"
                elif (s_idx + d_idx) % 5 == 0:
                    status_choice = "Late"
                    state_choice = "S3"
                    symbol = "L"
                else:
                    status_choice = "Present"
                    state_choice = "S1"
                    symbol = "P"

            final_state = "S4" if is_finalized else state_choice

            att_docs.append({
                "id": att_id,
                "student_id": s_idx,
                "subject_id": 1,
                "attendance_date": date_str,
                "status": status_choice,
                "automata_state": final_state,
                "marked_by": 2, # Grace Hopper
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            })

            log_docs.append({
                "id": log_id,
                "attendance_id": att_id,
                "previous_state": "S0",
                "input_symbol": symbol,
                "next_state": state_choice,
                "changed_by": 2,
                "reason": f"Initial faculty mark: {status_choice}",
                "timestamp": date_str + " 09:05:00"
            })
            log_id += 1

            if is_finalized:
                log_docs.append({
                    "id": log_id,
                    "attendance_id": att_id,
                    "previous_state": state_choice,
                    "input_symbol": "F",
                    "next_state": "S4",
                    "changed_by": 2,
                    "reason": "Session attendance finalized and locked",
                    "timestamp": date_str + " 10:00:00"
                })
                log_id += 1

            att_id += 1

    db.attendance.insert_many(att_docs)
    db.attendance_logs.insert_many(log_docs)
    db.counters.update_one({"_id": "attendance"}, {"$set": {"seq": att_id - 1}}, upsert=True)
    db.counters.update_one({"_id": "attendance_logs"}, {"$set": {"seq": log_id - 1}}, upsert=True)
    print(f"[SEED MONGODB] Inserted {len(att_docs)} attendance records and {len(log_docs)} DFA audit logs.")


def seed_sqlite():
    print("[SEED SQLITE] Checking if SQLite needs seeding...")
    existing = Database.query_one("SELECT COUNT(*) as count FROM users")
    if existing and existing["count"] > 0:
        return

    # Seed departments, admin, faculty, subjects, students
    dept_ids = {
        "CSE": Database.insert_and_get_id("INSERT INTO departments (department_name, department_code) VALUES ('Computer Science & Engineering', 'CSE')"),
        "ECE": Database.insert_and_get_id("INSERT INTO departments (department_name, department_code) VALUES ('Electronics & Communication Engineering', 'ECE')"),
        "IT": Database.insert_and_get_id("INSERT INTO departments (department_name, department_code) VALUES ('Information Technology', 'IT')")
    }

    admin_pw = generate_password_hash("admin123")
    Database.insert_and_get_id("INSERT INTO users (name, email, password, role) VALUES ('Dr. Alan Turing (System Administrator)', 'admin@college.edu', %s, 'admin')", (admin_pw,))

    faculty_data = [
        ("Prof. Grace Hopper", "faculty1@college.edu", "CSE", "Professor & HOD"),
        ("Prof. John von Neumann", "faculty2@college.edu", "CSE", "Associate Professor"),
        ("Prof. Claude Shannon", "faculty3@college.edu", "ECE", "Professor"),
        ("Prof. Ada Lovelace", "faculty4@college.edu", "IT", "Associate Professor"),
        ("Prof. Donald Knuth", "faculty5@college.edu", "IT", "Assistant Professor")
    ]
    fac_pw = generate_password_hash("faculty123")
    faculty_ids = {}
    for name, email, d_code, desig in faculty_data:
        u_id = Database.insert_and_get_id("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'faculty')", (name, email, fac_pw))
        f_id = Database.insert_and_get_id("INSERT INTO faculty (user_id, department_id, designation) VALUES (%s, %s, %s)", (u_id, dept_ids[d_code], desig))
        faculty_ids[email] = {"user_id": u_id, "faculty_id": f_id}

    subjects_data = [
        ("Theory of Computation & Automata", "CS301", "CSE", 5, 4),
        ("Database Management Systems", "CS302", "CSE", 5, 3),
        ("Digital Signal Processing", "EC301", "ECE", 5, 4),
        ("Microprocessors & Microcontrollers", "EC302", "ECE", 5, 3),
        ("Web Technologies & Frameworks", "IT301", "IT", 5, 4),
        ("Cloud Computing Architecture", "IT302", "IT", 5, 3)
    ]
    subject_ids = {}
    for s_name, s_code, d_code, sem, credits in subjects_data:
        s_id = Database.insert_and_get_id("INSERT INTO subjects (subject_name, subject_code, department_id, semester, credits) VALUES (%s, %s, %s, %s, %s)", (s_name, s_code, dept_ids[d_code], sem, credits))
        subject_ids[s_code] = s_id

    fac_subj_mappings = [
        ("faculty1@college.edu", "CS301"),
        ("faculty2@college.edu", "CS302"),
        ("faculty3@college.edu", "EC301"),
        ("faculty3@college.edu", "EC302"),
        ("faculty4@college.edu", "IT301"),
        ("faculty5@college.edu", "IT302")
    ]
    for fac_email, s_code in fac_subj_mappings:
        Database.execute("INSERT INTO faculty_subjects (faculty_id, subject_id) VALUES (%s, %s)", (faculty_ids[fac_email]["faculty_id"], subject_ids[s_code]))

    student_names = [
        ("Alice Walker", "student1@college.edu", "2024CSE001", "CSE", 5),
        ("Bob Miller", "student2@college.edu", "2024CSE002", "CSE", 5),
        ("Charlie Davis", "student3@college.edu", "2024CSE003", "CSE", 5),
        ("Diana Prince", "student4@college.edu", "2024CSE004", "CSE", 5),
        ("Ethan Hunt", "student5@college.edu", "2024CSE005", "CSE", 5),
        ("Fiona Gallagher", "student6@college.edu", "2024CSE006", "CSE", 5),
        ("George Clark", "student7@college.edu", "2024CSE007", "CSE", 5),
        ("Hannah Abbott", "student8@college.edu", "2024CSE008", "CSE", 5),
        ("Ian Wright", "student9@college.edu", "2024CSE009", "CSE", 5),
        ("Julia Roberts", "student10@college.edu", "2024CSE010", "CSE", 5),

        ("Kevin Peterson", "student11@college.edu", "2024ECE001", "ECE", 5),
        ("Laura Croft", "student12@college.edu", "2024ECE002", "ECE", 5),
        ("Michael Scott", "student13@college.edu", "2024ECE003", "ECE", 5),
        ("Nancy Wheeler", "student14@college.edu", "2024ECE004", "ECE", 5),
        ("Oliver Queen", "student15@college.edu", "2024ECE005", "ECE", 5),
        ("Peter Parker", "student16@college.edu", "2024ECE006", "ECE", 5),
        ("Quinn Fabray", "student17@college.edu", "2024ECE007", "ECE", 5),
        ("Rachel Green", "student18@college.edu", "2024ECE008", "ECE", 5),
        ("Steve Rogers", "student19@college.edu", "2024ECE009", "ECE", 5),
        ("Tony Stark", "student20@college.edu", "2024ECE010", "ECE", 5),

        ("Uma Thurman", "student21@college.edu", "2024IT001", "IT", 5),
        ("Victor Stone", "student22@college.edu", "2024IT002", "IT", 5),
        ("Wanda Maximoff", "student23@college.edu", "2024IT003", "IT", 5),
        ("Xavier Thorne", "student24@college.edu", "2024IT004", "IT", 5),
        ("Yara Greyjoy", "student25@college.edu", "2024IT005", "IT", 5),
        ("Zack Snyder", "student26@college.edu", "2024IT006", "IT", 5),
        ("Arthur Dent", "student27@college.edu", "2024IT007", "IT", 5),
        ("Beth Harmon", "student28@college.edu", "2024IT008", "IT", 5),
        ("Cedric Diggory", "student29@college.edu", "2024IT009", "IT", 5),
        ("Daisy Johnson", "student30@college.edu", "2024IT010", "IT", 5)
    ]
    stud_pw = generate_password_hash("student123")
    student_records = []
    for name, email, reg_no, d_code, sem in student_names:
        u_id = Database.insert_and_get_id("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'student')", (name, email, stud_pw))
        st_id = Database.insert_and_get_id("INSERT INTO students (user_id, register_number, department_id, semester) VALUES (%s, %s, %s, %s)", (u_id, reg_no, dept_ids[d_code], sem))
        student_records.append({"student_id": st_id, "user_id": u_id, "dept_code": d_code, "reg_no": reg_no})

        subjs = ["CS301", "CS302"] if d_code == "CSE" else (["EC301", "EC302"] if d_code == "ECE" else ["IT301", "IT302"])
        for sc in subjs:
            Database.execute("INSERT INTO enrollments (student_id, subject_id) VALUES (%s, %s)", (st_id, subject_ids[sc]))

    today = datetime.date.today()
    past_dates = [today - datetime.timedelta(days=i) for i in range(1, 8)]
    grace_user_id = faculty_ids["faculty1@college.edu"]["user_id"]
    cs301_id = subject_ids["CS301"]
    cse_students = [s for s in student_records if s["dept_code"] == "CSE"]

    for d_idx, att_date in enumerate(past_dates):
        date_str = att_date.strftime("%Y-%m-%d")
        is_finalized = (d_idx > 0)

        for s_idx, st in enumerate(cse_students):
            if st["reg_no"] == "2024CSE008":
                status_choice = "Absent" if (d_idx % 2 == 0) else "Late"
                state_choice = "S2" if status_choice == "Absent" else "S3"
                symbol = "A" if status_choice == "Absent" else "L"
            else:
                if (s_idx + d_idx) % 7 == 0:
                    status_choice = "Absent"
                    state_choice = "S2"
                    symbol = "A"
                elif (s_idx + d_idx) % 5 == 0:
                    status_choice = "Late"
                    state_choice = "S3"
                    symbol = "L"
                else:
                    status_choice = "Present"
                    state_choice = "S1"
                    symbol = "P"

            final_state = "S4" if is_finalized else state_choice
            att_id = Database.insert_and_get_id(
                "INSERT INTO attendance (student_id, subject_id, attendance_date, status, automata_state, marked_by) VALUES (%s, %s, %s, %s, %s, %s)",
                (st["student_id"], cs301_id, date_str, status_choice, final_state, grace_user_id)
            )
            Database.execute(
                "INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason) VALUES (%s, %s, %s, %s, %s, %s)",
                (att_id, "S0", symbol, state_choice, grace_user_id, f"Initial faculty mark: {status_choice}")
            )
            if is_finalized:
                Database.execute(
                    "INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason) VALUES (%s, %s, %s, %s, %s, %s)",
                    (att_id, state_choice, "F", "S4", grace_user_id, "Session attendance finalized and locked")
                )
    print("[SEED SQLITE] Seeding complete.")


def seed_all():
    if Database.is_mongo():
        seed_mongo()
    else:
        seed_sqlite()

if __name__ == "__main__":
    Database.init_database()
    seed_all()
