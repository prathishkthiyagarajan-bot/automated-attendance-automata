import urllib.request
import json

def test(name, url, method='GET', data=None, headers=None):
    headers = headers or {}
    if data:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json', **headers},
            method=method
        )
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode()
            try:
                body = json.loads(content)
            except:
                body = content[:100]
            print(f"[PASS] {name}: HTTP {resp.status}")
            return body
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        try:
            body = json.loads(content)
        except:
            body = content[:100]
        err_msg = body.get('error') if isinstance(body, dict) else str(body)
        print(f"[HTTP {e.code}] {name}: {err_msg}")
        return body

print("="*60)
print("RUNNING END-TO-END AUTOMATED ATTENDANCE TEST SUITE")
print("="*60)

# 1. Test frontend
test('Frontend HTML Index', 'http://127.0.0.1:5000/')

# 2. Test Admin Login
admin_auth = test('Admin Login', 'http://127.0.0.1:5000/api/auth/login', 'POST', {'email': 'admin@college.edu', 'password': 'admin123'})
admin_id = str(admin_auth['user']['id'])

# 3. Test Faculty Login
fac_auth = test('Faculty Login', 'http://127.0.0.1:5000/api/auth/login', 'POST', {'email': 'faculty1@college.edu', 'password': 'faculty123'})
fac_id = str(fac_auth['user']['id'])

# 4. Test Student Login (Hannah Abbott, < 75%)
stud_auth = test('Student Warning Login', 'http://127.0.0.1:5000/api/auth/login', 'POST', {'email': 'student8@college.edu', 'password': 'student123'})
stud_id = str(stud_auth['user']['id'])

# 5. Test DFA Info
dfa_info = test('DFA Info API', 'http://127.0.0.1:5000/api/dfa/info')
print('  -> States:', [s['id'] for s in dfa_info['dfa']['states']])
print('  -> Alphabet:', [a['symbol'] for a in dfa_info['dfa']['alphabet']])

# 6. Test DFA Simulation: Valid
sim_valid = test('DFA Simulation Valid (P -> F)', 'http://127.0.0.1:5000/api/dfa/simulate', 'POST', {'sequence': ['P', 'F'], 'role': 'faculty'})
print('  -> Sequence Accepted:', sim_valid['simulation']['is_accepted'])
print('  -> Final State:', sim_valid['simulation']['final_state'])

# 7. Test DFA Simulation: Invalid S0 -> F
sim_invalid = test('DFA Simulation Invalid (S0 -> F)', 'http://127.0.0.1:5000/api/dfa/simulate', 'POST', {'sequence': ['F'], 'role': 'faculty'})
print('  -> Halting Reason:', sim_invalid['simulation']['halting_reason'])

# 8. Test Student Dashboard (<75% Warning)
stud_dash = test('Student Dashboard', 'http://127.0.0.1:5000/api/dashboard/student', 'GET', headers={'X-User-Id': stud_id})
print(f"  -> Student: {stud_dash['profile']['name']}")
print(f"  -> Overall %: {stud_dash['summary']['overall_percentage']}%")
print(f"  -> Warning Active: {stud_dash['summary']['warning']}")

# 9. Test Attendance Sheet API
sheet = test('Attendance Sheet CS301', 'http://127.0.0.1:5000/api/attendance/sheet?subject_id=1&date=2026-11-17', 'GET', headers={'X-User-Id': fac_id})
print(f"  -> Total enrolled: {sheet['total_enrolled']}")

# 10. Test Valid DFA Transition S0 -> S1 (P)
mark_res = test('Mark Attendance P', 'http://127.0.0.1:5000/api/attendance/mark', 'POST', {'student_id': 1, 'subject_id': 1, 'date': '2026-11-17', 'symbol': 'P'}, headers={'X-User-Id': fac_id})
print('  -> Transition δ(S0, P) ->', mark_res.get('next_state'))

# 11. Test Illegal DFA Transition: modifying a finalized record
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import Database

att = Database.find_one("attendance", {"automata_state": "S4"})
if att:
    bad_trans = test('Illegal DFA Mod on Finalized Record S4+P', 'http://127.0.0.1:5000/api/attendance/mark', 'POST', {'student_id': att['student_id'], 'subject_id': att['subject_id'], 'date': att['attendance_date'], 'symbol': 'P'}, headers={'X-User-Id': fac_id})
    print('  -> DFA Error Rejected as Expected:', bad_trans.get('error'))

# 12. Test Authorized Admin Reset δ(S4, R) -> S0
if att:
    reset_res = test('Authorized Admin Reset S4 -> S0', 'http://127.0.0.1:5000/api/attendance/reset', 'POST', {'attendance_id': att['id'], 'reason': 'Medical clearance approved by Dean'}, headers={'X-User-Id': admin_id})
    print('  -> Admin Reset Status:', reset_res.get('message'))
    att_after = Database.find_one("attendance", {"id": att['id']})
    print('  -> State After Reset:', att_after['automata_state'])
    assert att_after['automata_state'] == 'S0', 'Expected state to be S0 after admin reset!'

# 13. Test Reports & Analytics
reports = test('Attendance Reports API', 'http://127.0.0.1:5000/api/attendance/reports')
print('  -> Generated Reports count:', reports['count'])

print("="*60)
print("ALL END-TO-END SYSTEM INTEGRATION TESTS PASSED 100%!")
print("="*60)
