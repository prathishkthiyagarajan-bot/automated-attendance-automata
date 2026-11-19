"""
Finite Automata (DFA) Engine for Automated Attendance Management
Formal Specification:
    M = (Q, Σ, δ, q0, F)
    Q = {S0, S1, S2, S3, S4}
        S0: Not Marked
        S1: Present
        S2: Absent
        S3: Late
        S4: Attendance Finalized
    Σ = {P, A, L, F, R}
        P: Mark Present
        A: Mark Absent
        L: Mark Late
        F: Finalize Attendance
        R: Authorized Reset (Admin only)
    q0 = S0
    F = {S4}
"""

from typing import Dict, Tuple, Optional, Any, List

class DFAState:
    S0 = "S0"  # Not Marked
    S1 = "S1"  # Present
    S2 = "S2"  # Absent
    S3 = "S3"  # Late
    S4 = "S4"  # Attendance Finalized

    NAMES = {
        S0: "Not Marked",
        S1: "Present",
        S2: "Absent",
        S3: "Late",
        S4: "Attendance Finalized"
    }

    COLORS = {
        S0: {"bg": "#9ca3af", "text": "#374151", "label": "Gray (Not Marked)"},
        S1: {"bg": "#10b981", "text": "#065f46", "label": "Green (Present)"},
        S2: {"bg": "#ef4444", "text": "#991b1b", "label": "Red (Absent)"},
        S3: {"bg": "#f59e0b", "text": "#92400e", "label": "Orange (Late)"},
        S4: {"bg": "#3b82f6", "text": "#1e40af", "label": "Blue (Finalized)"}
    }


class DFAAlphabet:
    P = "P"  # Mark Present
    A = "A"  # Mark Absent
    L = "L"  # Mark Late
    F = "F"  # Finalize Attendance
    R = "R"  # Authorized Reset

    DESCRIPTIONS = {
        P: "Mark Present",
        A: "Mark Absent",
        L: "Mark Late",
        F: "Finalize Attendance",
        R: "Authorized Admin Reset"
    }


class DFAResult:
    def __init__(self, valid: bool, next_state: Optional[str] = None, message: str = "", details: Optional[Dict[str, Any]] = None):
        self.valid = valid
        self.next_state = next_state
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "next_state": self.next_state,
            "next_state_name": DFAState.NAMES.get(self.next_state, "Unknown") if self.next_state else None,
            "message": self.message,
            "details": self.details
        }


class AttendanceDFA:
    """
    Deterministic Finite Automaton governing attendance states and transitions.
    """
    STATES = [DFAState.S0, DFAState.S1, DFAState.S2, DFAState.S3, DFAState.S4]
    ALPHABET = [DFAAlphabet.P, DFAAlphabet.A, DFAAlphabet.L, DFAAlphabet.F, DFAAlphabet.R]
    INITIAL_STATE = DFAState.S0
    FINAL_STATES = [DFAState.S4]

    # Explicit transition matrix: δ(state, symbol) -> (next_state, allowed_roles, description)
    # Roles allowed: 'faculty', 'admin'
    TRANSITIONS: Dict[Tuple[str, str], Dict[str, Any]] = {
        # Transitions from S0 (Not Marked)
        (DFAState.S0, DFAAlphabet.P): {
            "next": DFAState.S1,
            "roles": ["faculty", "admin"],
            "desc": "Mark Present for unmarked session"
        },
        (DFAState.S0, DFAAlphabet.A): {
            "next": DFAState.S2,
            "roles": ["faculty", "admin"],
            "desc": "Mark Absent for unmarked session"
        },
        (DFAState.S0, DFAAlphabet.L): {
            "next": DFAState.S3,
            "roles": ["faculty", "admin"],
            "desc": "Mark Late for unmarked session"
        },
        (DFAState.S0, DFAAlphabet.R): {
            "next": DFAState.S0,
            "roles": ["admin"],
            "desc": "Reset already unmarked session (Idempotent)"
        },

        # Transitions from S1 (Present)
        (DFAState.S1, DFAAlphabet.P): {
            "next": DFAState.S1,
            "roles": ["faculty", "admin"],
            "desc": "Confirm Present (Idempotent update)"
        },
        (DFAState.S1, DFAAlphabet.A): {
            "next": DFAState.S2,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Present -> Absent before finalization"
        },
        (DFAState.S1, DFAAlphabet.L): {
            "next": DFAState.S3,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Present -> Late before finalization"
        },
        (DFAState.S1, DFAAlphabet.F): {
            "next": DFAState.S4,
            "roles": ["faculty", "admin"],
            "desc": "Finalize attendance for session (Locks record)"
        },
        (DFAState.S1, DFAAlphabet.R): {
            "next": DFAState.S0,
            "roles": ["admin"],
            "desc": "Administrative reset of Present record to Unmarked"
        },

        # Transitions from S2 (Absent)
        (DFAState.S2, DFAAlphabet.P): {
            "next": DFAState.S1,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Absent -> Present before finalization"
        },
        (DFAState.S2, DFAAlphabet.A): {
            "next": DFAState.S2,
            "roles": ["faculty", "admin"],
            "desc": "Confirm Absent (Idempotent update)"
        },
        (DFAState.S2, DFAAlphabet.L): {
            "next": DFAState.S3,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Absent -> Late before finalization"
        },
        (DFAState.S2, DFAAlphabet.F): {
            "next": DFAState.S4,
            "roles": ["faculty", "admin"],
            "desc": "Finalize attendance for session (Locks record)"
        },
        (DFAState.S2, DFAAlphabet.R): {
            "next": DFAState.S0,
            "roles": ["admin"],
            "desc": "Administrative reset of Absent record to Unmarked"
        },

        # Transitions from S3 (Late)
        (DFAState.S3, DFAAlphabet.P): {
            "next": DFAState.S1,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Late -> Present before finalization"
        },
        (DFAState.S3, DFAAlphabet.A): {
            "next": DFAState.S2,
            "roles": ["faculty", "admin"],
            "desc": "Authorized faculty correction: Late -> Absent before finalization"
        },
        (DFAState.S3, DFAAlphabet.L): {
            "next": DFAState.S3,
            "roles": ["faculty", "admin"],
            "desc": "Confirm Late (Idempotent update)"
        },
        (DFAState.S3, DFAAlphabet.F): {
            "next": DFAState.S4,
            "roles": ["faculty", "admin"],
            "desc": "Finalize attendance for session (Locks record)"
        },
        (DFAState.S3, DFAAlphabet.R): {
            "next": DFAState.S0,
            "roles": ["admin"],
            "desc": "Administrative reset of Late record to Unmarked"
        },

        # Transitions from S4 (Attendance Finalized)
        # S4 is an absorbing state for standard inputs.
        # ONLY input 'R' performed by 'admin' with audit log is allowed to transition back to S0!
        (DFAState.S4, DFAAlphabet.R): {
            "next": DFAState.S0,
            "roles": ["admin"],
            "desc": "Authorized Admin Override Reset: Finalized -> Unmarked with mandatory audit trail"
        }
    }

    @classmethod
    def validate_transition(
        cls,
        current_state: str,
        input_symbol: str,
        user_role: str = "faculty",
        has_audit_reason: bool = False
    ) -> DFAResult:
        """
        Validates transition δ(current_state, input_symbol) according to the DFA definition.
        Enforces state integrity, input alphabet rules, role authorization, and audit requirements.
        """
        # 1. State validation
        if current_state not in cls.STATES:
            return DFAResult(
                valid=False,
                message=f"DFA Error: Current state '{current_state}' is not recognized in Q = {cls.STATES}."
            )

        # 2. Input symbol validation
        if input_symbol not in cls.ALPHABET:
            return DFAResult(
                valid=False,
                message=f"DFA Error: Input symbol '{input_symbol}' is not in alphabet Σ = {cls.ALPHABET}."
            )

        # 3. Special rule: S0 cannot be finalized directly
        if current_state == DFAState.S0 and input_symbol == DFAAlphabet.F:
            return DFAResult(
                valid=False,
                message="DFA Transition Rejected: Transition δ(S0, F) is undefined. Attendance cannot be finalized before student status is marked (P, A, or L)."
            )

        # 4. Check if transition exists in transition table
        transition_key = (current_state, input_symbol)
        if transition_key not in cls.TRANSITIONS:
            # Handle specific intuitive explanation for S4 locked state
            if current_state == DFAState.S4:
                return DFAResult(
                    valid=False,
                    message=f"DFA Transition Rejected: In state S4 (Attendance Finalized), input '{input_symbol}' is prohibited. Attendance is locked and immutable. Only an Administrator can execute Authorized Reset ('R') with an audit record.",
                    details={
                        "violation": "FINALIZED_STATE_IMMUTABILITY",
                        "current_state": current_state,
                        "attempted_symbol": input_symbol
                    }
                )
            return DFAResult(
                valid=False,
                message=f"DFA Transition Rejected: δ({current_state}, {input_symbol}) is not a valid transition in the attendance automaton.",
                details={
                    "violation": "UNDEFINED_TRANSITION",
                    "current_state": current_state,
                    "attempted_symbol": input_symbol
                }
            )

        rule = cls.TRANSITIONS[transition_key]
        allowed_roles = rule.get("roles", [])

        # 5. Role authorization check
        if user_role not in allowed_roles:
            return DFAResult(
                valid=False,
                message=f"DFA Authorization Error: Transition δ({current_state}, {input_symbol}) requires roles {allowed_roles}, but current user role is '{user_role}'.",
                details={
                    "violation": "INSUFFICIENT_ROLE_PRIVILEGES",
                    "required_roles": allowed_roles,
                    "user_role": user_role
                }
            )

        # 6. Admin reset requirements (S4 -> S0 requires an audit reason)
        if current_state == DFAState.S4 and input_symbol == DFAAlphabet.R:
            if not has_audit_reason:
                return DFAResult(
                    valid=False,
                    message="DFA Audit Requirement: Transition δ(S4, R) requires a documented administrative reason for auditing and compliance.",
                    details={
                        "violation": "MISSING_AUDIT_REASON"
                    }
                )

        next_state = rule["next"]
        return DFAResult(
            valid=True,
            next_state=next_state,
            message=f"DFA Transition Accepted: δ({current_state}, {input_symbol}) -> {next_state}. {rule['desc']}.",
            details={
                "previous_state": current_state,
                "input_symbol": input_symbol,
                "next_state": next_state,
                "description": rule["desc"]
            }
        )

    @classmethod
    def simulate_sequence(cls, initial_state: str, symbols: List[str], role: str = "admin") -> Dict[str, Any]:
        """
        Simulate a sequence of input symbols on the DFA starting from initial_state.
        Returns the step-by-step trace and whether the input string is accepted.
        """
        current = initial_state
        trace = []
        is_valid = True
        halting_reason = None

        trace.append({
            "step": 0,
            "state": current,
            "state_name": DFAState.NAMES.get(current, ""),
            "input": None,
            "valid": True,
            "message": f"Initial state: {current} ({DFAState.NAMES.get(current, '')})"
        })

        for i, sym in enumerate(symbols):
            res = cls.validate_transition(current, sym, user_role=role, has_audit_reason=True)
            if not res.valid:
                is_valid = False
                halting_reason = res.message
                trace.append({
                    "step": i + 1,
                    "state": current,
                    "state_name": DFAState.NAMES.get(current, ""),
                    "input": sym,
                    "valid": False,
                    "message": res.message
                })
                break
            else:
                current = res.next_state
                trace.append({
                    "step": i + 1,
                    "state": current,
                    "state_name": DFAState.NAMES.get(current, ""),
                    "input": sym,
                    "valid": True,
                    "message": res.message
                })

        return {
            "initial_state": initial_state,
            "input_sequence": symbols,
            "final_state": current,
            "is_accepted": is_valid and (current in cls.FINAL_STATES or current in cls.STATES),
            "is_finalized": current == DFAState.S4,
            "halting_reason": halting_reason,
            "trace": trace
        }

    @classmethod
    def get_formal_definition(cls) -> Dict[str, Any]:
        """
        Returns full formal definition of the DFA for visualization and API consumers.
        """
        transitions_list = []
        for (st, sym), rule in cls.TRANSITIONS.items():
            transitions_list.append({
                "from_state": st,
                "from_state_name": DFAState.NAMES[st],
                "input_symbol": sym,
                "input_name": DFAAlphabet.DESCRIPTIONS[sym],
                "to_state": rule["next"],
                "to_state_name": DFAState.NAMES[rule["next"]],
                "allowed_roles": rule["roles"],
                "description": rule["desc"]
            })

        return {
            "title": "Automated Attendance Finite Automaton",
            "formal_tuple": "M = (Q, Σ, δ, q0, F)",
            "states": [
                {"id": s, "name": DFAState.NAMES[s], "is_initial": (s == cls.INITIAL_STATE), "is_final": (s in cls.FINAL_STATES), "color": DFAState.COLORS[s]}
                for s in cls.STATES
            ],
            "alphabet": [
                {"symbol": a, "description": DFAAlphabet.DESCRIPTIONS[a]}
                for a in cls.ALPHABET
            ],
            "initial_state": cls.INITIAL_STATE,
            "final_states": cls.FINAL_STATES,
            "transitions": transitions_list
        }
