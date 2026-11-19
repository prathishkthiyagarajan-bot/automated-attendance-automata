"""
Seed Data Generator for Automated Attendance Management System Using Finite Automata
Generates:
- 1 Admin
- 3 Departments (CSE, ECE, IT)
- 5 Faculty Members
- 6 Subjects
- 30 Students
- Faculty Subject Assignments
- Student Subject Enrollments
- Realistic Attendance Records across past dates with DFA audit logs
"""

import datetime
from werkzeug.security import generate_password_hash
from database import Database

def seed_all():
    print("[SEED] Checking if database needs seeding...")
    existing = Database.query_one("SELECT COUNT(*) as count FROM users")
    if existing and existing["count"] > 0:
        print("[SEED] Database already contains users. Skipping seed.")
        return

    print("[SEED] Generating sample data...")

    # 1. Departments
    dept_data = [
        ("Computer Science & Engineering", "CSE"),
        ("Electronics & Communication Engineering", "ECE"),
        ("Information Technology", "IT")
    ]
    dept_ids = {}
    for name, code in dept_data:
        d_id = Database.insert_and_get_id(
            "INSERT INTO departments (department_name, department_code) VALUES (%s, %s)",
            (name, code)
        )
        dept_ids[code] = d_id
    print(f"[SEED] Inserted 3 departments: {dept_ids}")

    # 2. Admin User
    admin_pw = generate_password_hash("admin123")
    Database.insert_and_get_id(
        "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
        ("Dr. Alan Turing (System Administrator)", "admin@college.edu", admin_pw, "admin")
    )

    # 3. Faculty Users
    faculty_data = [
        ("Prof. Grace Hopper", "faculty1@college.edu", "CSE", "Professor & HOD"),
        ("Prof. John von Neumann", "faculty2@college.edu", "CSE", "Associate Professor"),
        ("Prof. Claude Shannon", "faculty3@college.edu", "ECE", "Professor"),
        ("Prof. Ada Lovelace", "faculty4@college.edu", "IT", "Associate Professor"),
        ("Prof. Donald Knuth", "faculty5@college.edu", "IT", "Assistant Professor")
    ]
    faculty_ids = {}
    fac_pw = generate_password_hash("faculty123")
    for name, email, dept_code, desig in faculty_data:
        u_id = Database.insert_and_get_id(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, fac_pw, "faculty")
        )
        f_id = Database.insert_and_get_id(
            "INSERT INTO faculty (user_id, department_id, designation) VALUES (%s, %s, %s)",
            (u_id, dept_ids[dept_code], desig)
        )
        faculty_ids[email] = {"user_id": u_id, "faculty_id": f_id, "dept_code": dept_code}
    print(f"[SEED] Inserted 5 faculty members.")

    # 4. Subjects
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
        s_id = Database.insert_and_get_id(
            "INSERT INTO subjects (subject_name, subject_code, department_id, semester, credits) VALUES (%s, %s, %s, %s, %s)",
            (s_name, s_code, dept_ids[d_code], sem, credits)
        )
        subject_ids[s_code] = s_id
    print(f"[SEED] Inserted 6 subjects.")

    # 5. Faculty Subject Assignments
    fac_subj_mappings = [
        ("faculty1@college.edu", "CS301"), # Grace Hopper -> CS301 (Theory of Computation & Automata)
        ("faculty2@college.edu", "CS302"), # John von Neumann -> CS302 (DBMS)
        ("faculty3@college.edu", "EC301"), # Claude Shannon -> EC301 (DSP)
        ("faculty3@college.edu", "EC302"), # Claude Shannon -> EC302 (Microprocessors)
        ("faculty4@college.edu", "IT301"), # Ada Lovelace -> IT301 (Web Tech)
        ("faculty5@college.edu", "IT302")  # Donald Knuth -> IT302 (Cloud Computing)
    ]
    for fac_email, s_code in fac_subj_mappings:
        Database.execute(
            "INSERT INTO faculty_subjects (faculty_id, subject_id) VALUES (%s, %s)",
            (faculty_ids[fac_email]["faculty_id"], subject_ids[s_code])
        )
    print(f"[SEED] Assigned subjects to faculty.")

    # 6. 30 Students (10 CSE, 10 ECE, 10 IT)
    student_names = [
        # CSE Students (1-10)
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

        # ECE Students (11-20)
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

        # IT Students (21-30)
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
        u_id = Database.insert_and_get_id(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, stud_pw, "student")
        )
        st_id = Database.insert_and_get_id(
            "INSERT INTO students (user_id, register_number, department_id, semester) VALUES (%s, %s, %s, %s)",
            (u_id, reg_no, dept_ids[d_code], sem)
        )
        student_records.append({
            "student_id": st_id,
            "user_id": u_id,
            "name": name,
            "email": email,
            "reg_no": reg_no,
            "dept_code": d_code
        })
    print(f"[SEED] Inserted 30 students.")

    # 7. Enrollments
    # Enroll CSE students in CS301 & CS302
    # Enroll ECE students in EC301 & EC302
    # Enroll IT students in IT301 & IT302
    for s in student_records:
        dept = s["dept_code"]
        if dept == "CSE":
            subjs = ["CS301", "CS302"]
        elif dept == "ECE":
            subjs = ["EC301", "EC302"]
        else:
            subjs = ["IT301", "IT302"]

        for sc in subjs:
            Database.execute(
                "INSERT INTO enrollments (student_id, subject_id) VALUES (%s, %s)",
                (s["student_id"], subject_ids[sc])
            )
    print(f"[SEED] Enrolled students in relevant department subjects.")

    # 8. Realistic Attendance Records with DFA States and Transition Logs
    # We will generate attendance for past 7 days for CS301 (Theory of Computation) and CS302 (DBMS)
    today = datetime.date.today()
    past_dates = [today - datetime.timedelta(days=i) for i in range(1, 8)]

    # Grace Hopper's user ID for CS301
    grace_user_id = faculty_ids["faculty1@college.edu"]["user_id"]
    cs301_id = subject_ids["CS301"]

    cse_students = [s for s in student_records if s["dept_code"] == "CSE"]

    # For dates 2 to 7 days ago: Mark and Finalize (S4)
    # Some students Present, some Absent, some Late to demonstrate percentage variations and warnings!
    for d_idx, att_date in enumerate(past_dates):
        date_str = att_date.strftime("%Y-%m-%d")
        is_finalized = (d_idx > 0) # Day 1 is left unfinalized or in progress for testing!

        for s_idx, st in enumerate(cse_students):
            # Student 1 (Alice) has high attendance (~90%)
            # Student 8 (Hannah) has low attendance (~60%) to trigger the < 75% warning indicator!
            if st["reg_no"] == "2024CSE008":
                # Low attendance student
                status_choice = "Absent" if (d_idx % 2 == 0) else "Late"
                state_choice = "S2" if status_choice == "Absent" else "S3"
                symbol = "A" if status_choice == "Absent" else "L"
            elif st["reg_no"] == "2024CSE009":
                # Borderline attendance student (~70%)
                status_choice = "Absent" if (d_idx in [1, 3, 5]) else "Present"
                state_choice = "S2" if status_choice == "Absent" else "S1"
                symbol = "A" if status_choice == "Absent" else "P"
            else:
                # Normal high attendance students
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
                """INSERT INTO attendance (student_id, subject_id, attendance_date, status, automata_state, marked_by)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (st["student_id"], cs301_id, date_str, status_choice, final_state, grace_user_id)
            )

            # Insert initial log: S0 -> state_choice
            Database.execute(
                """INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (att_id, "S0", symbol, state_choice, grace_user_id, f"Initial faculty mark: {status_choice}")
            )

            # If finalized, insert finalization log: state_choice -> S4
            if is_finalized:
                Database.execute(
                    """INSERT INTO attendance_logs (attendance_id, previous_state, input_symbol, next_state, changed_by, reason)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (att_id, state_choice, "F", "S4", grace_user_id, "Session attendance finalized and locked")
                )

    print(f"[SEED] Created historical attendance records and DFA transition audit logs.")
    print("[SEED] Seeding completed successfully!")

if __name__ == "__main__":
    Database.init_database()
    seed_all()
