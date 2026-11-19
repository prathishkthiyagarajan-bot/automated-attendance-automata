-- MySQL Sample Seed Script for Automated Attendance Management System Using Finite Automata
USE attendance_system;

-- 1. Departments
INSERT IGNORE INTO departments (id, department_name, department_code) VALUES
(1, 'Computer Science & Engineering', 'CSE'),
(2, 'Electronics & Communication Engineering', 'ECE'),
(3, 'Information Technology', 'IT');

-- 2. Users (Admin, Faculty, Students)
-- Passwords below are hashed using werkzeug/scrypt:
-- admin123, faculty123, student123
INSERT IGNORE INTO users (id, name, email, password, role) VALUES
(1, 'Dr. Alan Turing (System Administrator)', 'admin@college.edu', 'scrypt:32768:8:1$uH3G6kO0$766512d6cfba0dbad577eb0c8cb08044733db92cbe3cfba4e883e449911ea150c22629b39e6a9816007e1533cebbff088f7236526131c9bf9393a652e90956b6', 'admin'),
(2, 'Prof. Grace Hopper', 'faculty1@college.edu', 'scrypt:32768:8:1$7U60pLmq$431637ae7bf8e7dc7407077f59d43ad26f959c95d985a72db2f0b4d45d81b37985aa044b7f8c148ae8e001d9f8c679a9572cbf42e23d0473cefd7e0a294fc6b6', 'faculty'),
(3, 'Prof. John von Neumann', 'faculty2@college.edu', 'scrypt:32768:8:1$7U60pLmq$431637ae7bf8e7dc7407077f59d43ad26f959c95d985a72db2f0b4d45d81b37985aa044b7f8c148ae8e001d9f8c679a9572cbf42e23d0473cefd7e0a294fc6b6', 'faculty'),
(4, 'Prof. Claude Shannon', 'faculty3@college.edu', 'scrypt:32768:8:1$7U60pLmq$431637ae7bf8e7dc7407077f59d43ad26f959c95d985a72db2f0b4d45d81b37985aa044b7f8c148ae8e001d9f8c679a9572cbf42e23d0473cefd7e0a294fc6b6', 'faculty'),
(5, 'Prof. Ada Lovelace', 'faculty4@college.edu', 'scrypt:32768:8:1$7U60pLmq$431637ae7bf8e7dc7407077f59d43ad26f959c95d985a72db2f0b4d45d81b37985aa044b7f8c148ae8e001d9f8c679a9572cbf42e23d0473cefd7e0a294fc6b6', 'faculty'),
(6, 'Prof. Donald Knuth', 'faculty5@college.edu', 'scrypt:32768:8:1$7U60pLmq$431637ae7bf8e7dc7407077f59d43ad26f959c95d985a72db2f0b4d45d81b37985aa044b7f8c148ae8e001d9f8c679a9572cbf42e23d0473cefd7e0a294fc6b6', 'faculty');

-- 3. Faculty details
INSERT IGNORE INTO faculty (id, user_id, department_id, designation) VALUES
(1, 2, 1, 'Professor & HOD'),
(2, 3, 1, 'Associate Professor'),
(3, 4, 2, 'Professor'),
(4, 5, 3, 'Associate Professor'),
(5, 6, 3, 'Assistant Professor');

-- 4. Subjects
INSERT IGNORE INTO subjects (id, subject_name, subject_code, department_id, semester, credits) VALUES
(1, 'Theory of Computation & Automata', 'CS301', 1, 5, 4),
(2, 'Database Management Systems', 'CS302', 1, 5, 3),
(3, 'Digital Signal Processing', 'EC301', 2, 5, 4),
(4, 'Microprocessors & Microcontrollers', 'EC302', 2, 5, 3),
(5, 'Web Technologies & Frameworks', 'IT301', 3, 5, 4),
(6, 'Cloud Computing Architecture', 'IT302', 3, 5, 3);

-- 5. Faculty Subjects
INSERT IGNORE INTO faculty_subjects (faculty_id, subject_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(3, 4),
(4, 5),
(5, 6);
