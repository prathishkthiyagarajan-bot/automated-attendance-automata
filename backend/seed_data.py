"""Seed the MongoDB collections with demo attendance data."""

import datetime

from werkzeug.security import generate_password_hash

from database import Database


def seed_all():
    print("[SEED] Checking if database needs seeding...")
    if Database.count("users"):
        print("[SEED] Database already contains users. Skipping seed.")
        return

    departments = [
        ("Computer Science & Engineering", "CSE"),
        ("Electronics & Communication Engineering", "ECE"),
        ("Information Technology", "IT"),
    ]
    department_ids = {}
    for name, code in departments:
        department_ids[code] = Database.insert(
            "departments", {"department_name": name, "department_code": code}
        )

    Database.insert(
        "users",
        {
            "name": "Dr. Alan Turing (System Administrator)",
            "email": "admin@college.edu",
            "password": generate_password_hash("admin123"),
            "role": "admin",
        },
    )

    faculty_data = [
        ("Prof. Grace Hopper", "faculty1@college.edu", "CSE", "Professor & HOD"),
        ("Prof. John von Neumann", "faculty2@college.edu", "CSE", "Associate Professor"),
        ("Prof. Claude Shannon", "faculty3@college.edu", "ECE", "Professor"),
        ("Prof. Ada Lovelace", "faculty4@college.edu", "IT", "Associate Professor"),
        ("Prof. Donald Knuth", "faculty5@college.edu", "IT", "Assistant Professor"),
    ]
    faculty_ids = {}
    faculty_password = generate_password_hash("faculty123")
    for name, email, department_code, designation in faculty_data:
        user_id = Database.insert(
            "users",
            {
                "name": name,
                "email": email,
                "password": faculty_password,
                "role": "faculty",
            },
        )
        faculty_id = Database.insert(
            "faculty",
            {
                "user_id": user_id,
                "department_id": department_ids[department_code],
                "designation": designation,
            },
        )
        faculty_ids[email] = {"user_id": user_id, "faculty_id": faculty_id}

    subjects_data = [
        ("Theory of Computation & Automata", "CS301", "CSE", 5, 4),
        ("Database Management Systems", "CS302", "CSE", 5, 3),
        ("Digital Signal Processing", "EC301", "ECE", 5, 4),
        ("Microprocessors & Microcontrollers", "EC302", "ECE", 5, 3),
        ("Web Technologies & Frameworks", "IT301", "IT", 5, 4),
        ("Cloud Computing Architecture", "IT302", "IT", 5, 3),
    ]
    subject_ids = {}
    for name, code, department_code, semester, credits in subjects_data:
        subject_ids[code] = Database.insert(
            "subjects",
            {
                "subject_name": name,
                "subject_code": code,
                "department_id": department_ids[department_code],
                "semester": semester,
                "credits": credits,
            },
        )

    faculty_subjects = [
        ("faculty1@college.edu", "CS301"),
        ("faculty2@college.edu", "CS302"),
        ("faculty3@college.edu", "EC301"),
        ("faculty3@college.edu", "EC302"),
        ("faculty4@college.edu", "IT301"),
        ("faculty5@college.edu", "IT302"),
    ]
    for email, subject_code in faculty_subjects:
        Database.insert(
            "faculty_subjects",
            {
                "faculty_id": faculty_ids[email]["faculty_id"],
                "subject_id": subject_ids[subject_code],
            },
        )

    student_names = [
        ("Alice Walker", "student1", "CSE", 1),
        ("Bob Miller", "student2", "CSE", 2),
        ("Charlie Davis", "student3", "CSE", 3),
        ("Diana Prince", "student4", "CSE", 4),
        ("Ethan Hunt", "student5", "CSE", 5),
        ("Fiona Gallagher", "student6", "CSE", 6),
        ("George Clark", "student7", "CSE", 7),
        ("Hannah Abbott", "student8", "CSE", 8),
        ("Ian Wright", "student9", "CSE", 9),
        ("Julia Roberts", "student10", "CSE", 10),
        ("Kevin Peterson", "student11", "ECE", 1),
        ("Laura Croft", "student12", "ECE", 2),
        ("Michael Scott", "student13", "ECE", 3),
        ("Nancy Wheeler", "student14", "ECE", 4),
        ("Oliver Queen", "student15", "ECE", 5),
        ("Peter Parker", "student16", "ECE", 6),
        ("Quinn Fabray", "student17", "ECE", 7),
        ("Rachel Green", "student18", "ECE", 8),
        ("Steve Rogers", "student19", "ECE", 9),
        ("Tony Stark", "student20", "ECE", 10),
        ("Uma Thurman", "student21", "IT", 1),
        ("Victor Stone", "student22", "IT", 2),
        ("Wanda Maximoff", "student23", "IT", 3),
        ("Xavier Thorne", "student24", "IT", 4),
        ("Yara Greyjoy", "student25", "IT", 5),
        ("Zack Snyder", "student26", "IT", 6),
        ("Arthur Dent", "student27", "IT", 7),
        ("Beth Harmon", "student28", "IT", 8),
        ("Cedric Diggory", "student29", "IT", 9),
        ("Daisy Johnson", "student30", "IT", 10),
    ]
    student_records = []
    student_password = generate_password_hash("student123")
    for name, email_prefix, department_code, number in student_names:
        email = f"{email_prefix}@college.edu"
        register_number = f"2024{department_code}{number:03}"
        user_id = Database.insert(
            "users",
            {
                "name": name,
                "email": email,
                "password": student_password,
                "role": "student",
            },
        )
        student_id = Database.insert(
            "students",
            {
                "user_id": user_id,
                "register_number": register_number,
                "department_id": department_ids[department_code],
                "semester": 5,
            },
        )
        student_records.append(
            {
                "student_id": student_id,
                "user_id": user_id,
                "register_number": register_number,
                "department_code": department_code,
            }
        )

        subject_codes = {
            "CSE": ("CS301", "CS302"),
            "ECE": ("EC301", "EC302"),
            "IT": ("IT301", "IT302"),
        }[department_code]
        for subject_code in subject_codes:
            Database.insert(
                "enrollments",
                {"student_id": student_id, "subject_id": subject_ids[subject_code]},
            )

    grace_user_id = faculty_ids["faculty1@college.edu"]["user_id"]
    today = datetime.date.today()
    past_dates = [today - datetime.timedelta(days=day) for day in range(1, 8)]
    cse_students = [s for s in student_records if s["department_code"] == "CSE"]

    for day_index, attendance_date in enumerate(past_dates):
        date_string = attendance_date.strftime("%Y-%m-%d")
        finalized = day_index > 0
        for student_index, student in enumerate(cse_students):
            if student["register_number"] == "2024CSE008":
                status = "Absent" if day_index % 2 == 0 else "Late"
            elif student["register_number"] == "2024CSE009":
                status = "Absent" if day_index in (1, 3, 5) else "Present"
            elif (student_index + day_index) % 7 == 0:
                status = "Absent"
            elif (student_index + day_index) % 5 == 0:
                status = "Late"
            else:
                status = "Present"

            state = {"Present": "S1", "Absent": "S2", "Late": "S3"}[status]
            symbol = {"Present": "P", "Absent": "A", "Late": "L"}[status]
            attendance_id = Database.insert(
                "attendance",
                {
                    "student_id": student["student_id"],
                    "subject_id": subject_ids["CS301"],
                    "attendance_date": date_string,
                    "status": status,
                    "automata_state": "S4" if finalized else state,
                    "marked_by": grace_user_id,
                },
            )
            Database.insert(
                "attendance_logs",
                {
                    "attendance_id": attendance_id,
                    "previous_state": "S0",
                    "input_symbol": symbol,
                    "next_state": state,
                    "changed_by": grace_user_id,
                    "reason": f"Initial faculty mark: {status}",
                },
            )
            if finalized:
                Database.insert(
                    "attendance_logs",
                    {
                        "attendance_id": attendance_id,
                        "previous_state": state,
                        "input_symbol": "F",
                        "next_state": "S4",
                        "changed_by": grace_user_id,
                        "reason": "Session attendance finalized and locked",
                    },
                )

    print("[SEED] Demo data seeded successfully.")


if __name__ == "__main__":
    Database.init_database()
    seed_all()
