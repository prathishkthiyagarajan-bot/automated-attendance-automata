# Automated Attendance Management System Using Finite Automata

A modern, responsive, full-stack web application developed for college attendance management across departments, strictly governed by a **Deterministic Finite Automaton (DFA)** to validate attendance states, eliminate unauthorized modifications, and maintain audit trails.

---

## 1. Mathematical Formulation: Deterministic Finite Automaton (DFA)

The attendance lifecycle is formally defined by the 5-tuple:

$$M = (Q, \Sigma, \delta, q_0, F)$$

### States ($Q$)
* **$S_0$ (Not Marked)**: Initial state ($q_0$). Session created but student attendance has not been registered.
* **$S_1$ (Present)**: Student is marked Present.
* **$S_2$ (Absent)**: Student is marked Absent.
* **$S_3$ (Late)**: Student is marked Late.
* **$S_4$ (Attendance Finalized)**: Terminal/Accepting state ($F$). Session is formally closed and immutable.

### Alphabet ($\Sigma$)
* **$P$**: Mark Present
* **$A$**: Mark Absent
* **$L$**: Mark Late
* **$F$**: Finalize Attendance
* **$R$**: Authorized Admin Reset

### State Transition Function ($\delta$)
$$\delta: Q \times \Sigma \to Q \cup \{\text{REJECT}\}$$

| State / Input | **P (Present)** | **A (Absent)** | **L (Late)** | **F (Finalize)** | **R (Admin Reset)** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **$S_0$ (Not Marked)** | $S_1$ | $S_2$ | $S_3$ | **REJECTED** (Premature Finalization) | $S_0$ (Idempotent) |
| **$S_1$ (Present)** | $S_1$ (Confirm) | $S_2$ (Correction) | $S_3$ (Correction) | $S_4$ (Lock) | $S_0$ (Admin Only) |
| **$S_2$ (Absent)** | $S_1$ (Correction) | $S_2$ (Confirm) | $S_3$ (Correction) | $S_4$ (Lock) | $S_0$ (Admin Only) |
| **$S_3$ (Late)** | $S_1$ (Correction) | $S_2$ (Correction) | $S_3$ (Confirm) | $S_4$ (Lock) | $S_0$ (Admin Only) |
| **$S_4$ (Finalized)** | **REJECTED** (Locked) | **REJECTED** (Locked) | **REJECTED** (Locked) | **REJECTED** (Locked) | $S_0$ (**Authorized Admin Reset Only**) |

### Core Mathematical Invariants
1. **No Premature Finalization**: $\delta(S_0, F)$ is undefined. A session cannot be finalized if any student remains in state $S_0$.
2. **Post-Finalization Immutability**: For any $\sigma \in \{P, A, L, F\}$, $\delta(S_4, \sigma) = \text{REJECT}$. Once locked, neither faculty nor students can tamper with the records.
3. **Authorized Reset with Audit Trail**: The transition $\delta(S_4, R) \to S_0$ is restricted strictly to users with the `admin` role and requires a documented justification recorded in the `attendance_logs` ledger.

---

## 2. Technology Stack

* **Frontend**:
  * React 18 (Component Architecture & Reactive State)
  * Tailwind CSS (Responsive Utility-First Styling with Dark Mode)
  * Chart.js (Department Attendance Performance & DFA State Distribution)
  * FontAwesome 6 (Vector Icons)
* **Backend**:
  * Python 3 Flask RESTful API
  * Pure Object-Oriented DFA Engine (`backend/dfa_engine.py`)
  * Werkzeug Security (Scrypt Password Hashing)
  * CORS & Custom Auth Tokens
* **Database**:
  * MongoDB
  * One-time migration from the legacy SQLite database (`attendance.db`)

---

## 3. User Roles & Capabilities

### 👑 Administrator
* Manage Departments (CSE, ECE, IT, etc.)
* Manage Faculty accounts and subject assignments
* Manage Student accounts and enrollments
* Department-wide analytics, attendance metrics, and compliance charts
* Interactive DFA State Machine Visualizer and Automaton Simulator
* Full Audit Log Inspection & Authorized Admin Reset ($\delta(S_4, R) \to S_0$)

### 👩‍🏫 Faculty
* View assigned subjects, class schedules, and enrolled student rosters
* Select department, subject, semester, and session date
* Mark attendance with inputs $P$ (Present), $A$ (Absent), $L$ (Late)
* Make pre-finalization corrections as permitted by the DFA
* Finalize attendance ($F$) to transition session to $S_4$
* View daily and monthly attendance analytics and export reports in **CSV format**

### 🎓 Student
* Personal profile, register number, and enrolled subjects
* Subject-wise attendance breakdown (Conducted, Present, Absent, Late)
* Overall attendance percentage meter
* **Automated Critical Warning Alert** whenever attendance falls below **75%**, including remedial calculation of required consecutive classes
* Monthly historical attendance trend graph

---

## 4. Attendance Percentage & Warning Calculation

$$\text{Attendance Percentage} = \left( \frac{\text{Conducted Classes Attended (Present)}}{\text{Total Conducted Classes}} \right) \times 100$$

### Critical Warning Remedial Formula
When $\text{Attendance} < 75\%$, the system computes the exact minimum number of consecutive classes ($k$) the student must attend to regain $\ge 75\%$:

$$\frac{\text{Present} + k}{\text{Total} + k} \ge 0.75 \implies k \ge 3 \times \text{Total} - 4 \times \text{Present}$$

---

## 5. Demo Login Credentials

| Role | Email | Password | Name / Notes |
|:---|:---|:---|:---|
| **System Administrator** | `admin@college.edu` | `admin123` | Dr. Alan Turing (Full Admin Privileges) |
| **Faculty (CSE)** | `faculty1@college.edu` | `faculty123` | Prof. Grace Hopper (CS301 - Theory of Computation) |
| **Faculty (CSE)** | `faculty2@college.edu` | `faculty123` | Prof. John von Neumann (CS302 - DBMS) |
| **Faculty (ECE)** | `faculty3@college.edu` | `faculty123` | Prof. Claude Shannon (EC301 - DSP, EC302) |
| **Faculty (IT)** | `faculty4@college.edu` | `faculty123` | Prof. Ada Lovelace (IT301 - Web Tech) |
| **Student (Normal)** | `student1@college.edu` | `student123` | Alice Walker (CSE, 90% Attendance) |
| **Student (Warning)** | `student8@college.edu` | `student123` | Hannah Abbott (CSE, &lt;75% Attendance Warning) |

---

## 6. Installation & Execution Guide

### Prerequisites
* Python 3.9 or higher
* MongoDB running locally, or a MongoDB connection URI

### Quick Start
```bash
# 1. Clone or navigate to the project directory
cd automated-attendance-automata

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure MONGODB_URI and MONGODB_DATABASE in .env

# 4. Launch application
python run.py
```
On first startup, existing records in `attendance.db` are copied to MongoDB with
their numeric IDs and relationships preserved. The SQLite file is left unchanged;
the migration marker prevents importing it again on subsequent starts. If there
is no legacy SQLite data, the application seeds MongoDB with the demo accounts.
Open your browser at **http://127.0.0.1:5000**.

---

## 7. Running Unit Tests

Run the DFA Finite Automata test suite to mathematically verify all transitions:
```bash
python backend/tests/test_dfa.py
```
Outputs:
```text
[TEST] Testing S0 (Not Marked) transitions...
  -> S0 transitions passed.
[TEST] Testing intermediate state corrections before finalization...
  -> Intermediate transitions passed.
[TEST] Testing Finalization (F) transitions...
  -> Finalization transitions passed.
[TEST] Testing S4 (Attendance Finalized) immutability and reset rules...
  -> S4 immutability and reset tests passed.
[TEST] Testing sequence simulation...
  -> Sequence simulation passed.

ALL DFA FINITE AUTOMATA UNIT TESTS PASSED SUCCESSFULLY! (100% PASS)
```
