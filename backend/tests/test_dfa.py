"""
Unit Tests for DFA Validation Engine
"""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dfa_engine import AttendanceDFA, DFAState, DFAAlphabet

def test_s0_transitions():
    print("[TEST] Testing S0 (Not Marked) transitions...")
    # S0 + P -> S1
    r = AttendanceDFA.validate_transition(DFAState.S0, DFAAlphabet.P, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S1, f"Failed: {r.message}"
    
    # S0 + A -> S2
    r = AttendanceDFA.validate_transition(DFAState.S0, DFAAlphabet.A, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S2, f"Failed: {r.message}"

    # S0 + L -> S3
    r = AttendanceDFA.validate_transition(DFAState.S0, DFAAlphabet.L, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S3, f"Failed: {r.message}"

    # S0 + F -> REJECTED (cannot finalize without marking)
    r = AttendanceDFA.validate_transition(DFAState.S0, DFAAlphabet.F, user_role="faculty")
    assert not r.valid, "S0 + F should be rejected!"
    print("  -> S0 transitions passed.")

def test_intermediate_transitions():
    print("[TEST] Testing intermediate state corrections before finalization...")
    # S1 (Present) -> A -> S2 (Absent)
    r = AttendanceDFA.validate_transition(DFAState.S1, DFAAlphabet.A, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S2

    # S2 (Absent) -> L -> S3 (Late)
    r = AttendanceDFA.validate_transition(DFAState.S2, DFAAlphabet.L, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S3

    # S3 (Late) -> P -> S1 (Present)
    r = AttendanceDFA.validate_transition(DFAState.S3, DFAAlphabet.P, user_role="faculty")
    assert r.valid and r.next_state == DFAState.S1
    print("  -> Intermediate transitions passed.")

def test_finalization_transitions():
    print("[TEST] Testing Finalization (F) transitions...")
    # S1 + F -> S4
    r1 = AttendanceDFA.validate_transition(DFAState.S1, DFAAlphabet.F, user_role="faculty")
    assert r1.valid and r1.next_state == DFAState.S4

    # S2 + F -> S4
    r2 = AttendanceDFA.validate_transition(DFAState.S2, DFAAlphabet.F, user_role="faculty")
    assert r2.valid and r2.next_state == DFAState.S4

    # S3 + F -> S4
    r3 = AttendanceDFA.validate_transition(DFAState.S3, DFAAlphabet.F, user_role="faculty")
    assert r3.valid and r3.next_state == DFAState.S4
    print("  -> Finalization transitions passed.")

def test_s4_immutability_and_reset():
    print("[TEST] Testing S4 (Attendance Finalized) immutability and reset rules...")
    # S4 + P must be REJECTED
    r_p = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.P, user_role="faculty")
    assert not r_p.valid, "S4 + P must be rejected"

    # S4 + A must be REJECTED
    r_a = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.A, user_role="faculty")
    assert not r_a.valid, "S4 + A must be rejected"

    # S4 + L must be REJECTED
    r_l = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.L, user_role="faculty")
    assert not r_l.valid, "S4 + L must be rejected"

    # S4 + F must be REJECTED
    r_f = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.F, user_role="faculty")
    assert not r_f.valid, "S4 + F must be rejected"

    # S4 + R by faculty must be REJECTED (only admin allowed)
    r_rf = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.R, user_role="faculty", has_audit_reason=True)
    assert not r_rf.valid, "S4 + R by faculty must be rejected"

    # S4 + R by admin WITHOUT reason must be REJECTED
    r_r_no_reason = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.R, user_role="admin", has_audit_reason=False)
    assert not r_r_no_reason.valid, "S4 + R without audit reason must be rejected"

    # S4 + R by admin WITH reason must SUCCEED -> S0
    r_r_ok = AttendanceDFA.validate_transition(DFAState.S4, DFAAlphabet.R, user_role="admin", has_audit_reason=True)
    assert r_r_ok.valid and r_r_ok.next_state == DFAState.S0, f"Expected S0 but got {r_r_ok.next_state}"
    print("  -> S4 immutability and reset tests passed.")

def test_sequence_simulation():
    print("[TEST] Testing sequence simulation...")
    # S0 -> P -> L -> A -> F should end in S4
    res = AttendanceDFA.simulate_sequence(DFAState.S0, ["P", "L", "A", "F"])
    assert res["is_accepted"] and res["final_state"] == DFAState.S4

    # S0 -> F should fail immediately at step 1
    res_fail = AttendanceDFA.simulate_sequence(DFAState.S0, ["F"])
    assert not res_fail["is_accepted"]
    print("  -> Sequence simulation passed.")

if __name__ == "__main__":
    test_s0_transitions()
    test_intermediate_transitions()
    test_finalization_transitions()
    test_s4_immutability_and_reset()
    test_sequence_simulation()
    print("\nALL DFA FINITE AUTOMATA UNIT TESTS PASSED SUCCESSFULLY! (100% PASS)")
