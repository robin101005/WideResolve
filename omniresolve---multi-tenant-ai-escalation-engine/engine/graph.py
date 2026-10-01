"""
LangGraph / StateGraph Orchestrator for OmniResolve.
Connects agents in strict order:
Intent -> History -> Order -> Policy -> Root Cause -> Resolution -> Escalation Gate.
Manages state transitions (AUTO_RESOLVE, WAITING_APPROVAL, ESCALATED),
approval actions, timeout escalations, and audit logging.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from engine.types import CaseFile, EscalationOutcome, RefundRequest
from agents.intent_agent import intent_agent
from agents.history_agent import history_agent
from agents.order_agent import order_agent
from agents.policy_agent import policy_agent
from agents.root_cause_agent import root_cause_agent
from agents.resolution_agent import resolution_agent
from engine.escalation_gate import escalation_gate
from engine.audit_chain import audit_chain, generate_case_brief
from engine.tools import issue_refund, get_db_connection

# In-memory case registry for rapid lookups and state management
ACTIVE_CASES: Dict[str, CaseFile] = {}

class ResolutionGraph:
    def __init__(self):
        self.intent_agent = intent_agent
        self.history_agent = history_agent
        self.order_agent = order_agent
        self.policy_agent = policy_agent
        self.root_cause_agent = root_cause_agent
        self.resolution_agent = resolution_agent
        self.escalation_gate = escalation_gate
        self.audit_chain = audit_chain

    def run(
        self,
        client_id: str,
        customer_id: str,
        raw_complaint: str,
        order_id: Optional[str] = None,
        conn=None
    ) -> CaseFile:
        """
        Executes the full pipeline:
        1. Intent Classification (with PII scrubbing)
        2. Customer History Analysis
        3. Order/Transaction Diagnostics
        4. Policy Retrieval (RAG)
        5. Root Cause Formulation & Margin Calculation
        6. Resolution Formulation
        7. Escalation Gate Evaluation
        8. Audit Logging & Outcome Execution
        """
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.utcnow().isoformat()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        try:
            case_file = CaseFile(
                case_id=case_id,
                client_id=client_id.lower(),
                customer_id=customer_id,
                order_id=order_id,
                raw_complaint=raw_complaint,
                created_at=now_str
            )

            # --- Node 1: Intent Agent ---
            intent_result = self.intent_agent.parse_intent(raw_complaint, client_id)
            case_file.sanitized_complaint = intent_result["sanitized_text"]
            case_file.intent = intent_result

            # Extract order ID if not explicitly provided
            if not case_file.order_id and intent_result.get("entities", {}).get("order_id"):
                case_file.order_id = intent_result["entities"]["order_id"]

            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="INTENT_CLASSIFIED",
                payload_data={
                    "issue_type": intent_result["issue_type"],
                    "sentiment": intent_result["sentiment"],
                    "urgency": intent_result["urgency"],
                    "legal_threat": intent_result["legal_threat"],
                    "fraud_claim": intent_result["fraud_claim"],
                    "medical_mention": intent_result["medical_mention"]
                },
                conn=conn
            )

            # --- Node 2: Customer History Agent ---
            self.history_agent.analyze(case_file, conn=conn)
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="HISTORY_ANALYZED",
                payload_data=case_file.customer_profile,
                conn=conn
            )

            # --- Node 3: Order/Transaction Agent ---
            self.order_agent.analyze(case_file, conn=conn)
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="ORDER_DIAGNOSED",
                payload_data={
                    "order_found": case_file.order_details.get("order_found"),
                    "duplicate_charges": case_file.order_details.get("duplicate_charges_found"),
                    "contradictions": case_file.order_details.get("contradictions"),
                    "evidence_agreement": case_file.order_details.get("evidence_agreement")
                },
                conn=conn
            )

            # --- Node 4: Policy / RAG Agent ---
            self.policy_agent.evaluate_policies(case_file)
            top_policy = case_file.relevant_policies[0] if case_file.relevant_policies else None
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="POLICY_MATCHED",
                payload_data={
                    "top_citation": top_policy.get("citation") if top_policy else "None",
                    "similarity_score": top_policy.get("similarity_score") if top_policy else 0.0
                },
                conn=conn
            )

            # --- Node 5: Root Cause Agent ---
            self.root_cause_agent.diagnose(case_file)
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="ROOT_CAUSE_DIAGNOSED",
                payload_data={
                    "top_hypothesis": case_file.root_cause_hypotheses[0]["hypothesis"] if case_file.root_cause_hypotheses else "",
                    "root_cause_margin": case_file.root_cause_margin
                },
                conn=conn
            )

            # --- Node 6: Resolution Agent ---
            self.resolution_agent.formulate_resolution(case_file)
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="RESOLUTION_FORMULATED",
                payload_data=case_file.proposed_resolution,
                conn=conn
            )

            # --- Node 7: Escalation Gate ---
            decision = self.escalation_gate.evaluate(case_file, conn=conn)
            self.audit_chain.append_log(
                client_id=case_file.client_id,
                case_id=case_id,
                action="ESCALATION_GATE_DECISION",
                payload_data=decision,
                conn=conn
            )

            # --- Final Execution & State Transitions ---
            outcome = decision["outcome"]
            amount = float(case_file.proposed_resolution.get("amount", 0.0))

            if outcome == EscalationOutcome.AUTO_RESOLVE.value:
                # Execute financial resolution if needed
                if amount > 0 and case_file.order_id:
                    issue_refund(
                        client_id=case_file.client_id,
                        order_id=case_file.order_id,
                        amount=amount,
                        reason=case_file.proposed_resolution.get("policy_citation", "Autonomous resolution"),
                        approved_by="SYSTEM_AUTO_RESOLVER",
                        conn=conn
                    )
                    self.audit_chain.append_log(
                        client_id=case_file.client_id,
                        case_id=case_id,
                        action="AUTO_REFUND_EXECUTED",
                        payload_data={
                            "order_id": case_file.order_id,
                            "amount": amount,
                            "status": "Completed"
                        },
                        conn=conn
                    )
                case_file.status = "AUTO_RESOLVED"

            elif outcome == EscalationOutcome.RESOLVE_WITH_APPROVAL.value:
                case_file.status = "WAITING_APPROVAL"
                case_file.case_brief = generate_case_brief(case_file)

            else:  # ESCALATE
                case_file.status = "ESCALATED"
                case_file.case_brief = generate_case_brief(case_file)

            # Store in active memory
            ACTIVE_CASES[case_id] = case_file
            return case_file

        finally:
            if close_conn:
                conn.close()

    def approve_case(self, case_id: str, approver_id: str, conn=None) -> Dict[str, Any]:
        """Human manager approves case in WAITING_APPROVAL state."""
        if case_id not in ACTIVE_CASES:
            return {"success": False, "error": f"Case {case_id} not found."}

        case = ACTIVE_CASES[case_id]
        if case.status != "WAITING_APPROVAL":
            return {"success": False, "error": f"Case {case_id} is in status '{case.status}', not 'WAITING_APPROVAL'."}

        amount = float(case.proposed_resolution.get("amount", 0.0))
        if amount > 0 and case.order_id:
            issue_refund(
                client_id=case.client_id,
                order_id=case.order_id,
                amount=amount,
                reason=case.proposed_resolution.get("policy_citation", "Manager approved"),
                approved_by=approver_id,
                conn=conn
            )

        case.status = "APPROVED_AND_RESOLVED"
        self.audit_chain.append_log(
            client_id=case.client_id,
            case_id=case_id,
            action="CASE_APPROVED_BY_HUMAN",
            payload_data={"approver_id": approver_id, "amount": amount, "timestamp": datetime.utcnow().isoformat()},
            conn=conn
        )
        return {"success": True, "case_id": case_id, "status": "APPROVED_AND_RESOLVED", "amount": amount}

    def reject_case(self, case_id: str, rejecter_id: str, reason: str, conn=None) -> Dict[str, Any]:
        """Human manager rejects proposed resolution."""
        if case_id not in ACTIVE_CASES:
            return {"success": False, "error": f"Case {case_id} not found."}

        case = ACTIVE_CASES[case_id]
        case.status = "REJECTED"
        self.audit_chain.append_log(
            client_id=case.client_id,
            case_id=case_id,
            action="CASE_REJECTED_BY_HUMAN",
            payload_data={"rejecter_id": rejecter_id, "reason": reason, "timestamp": datetime.utcnow().isoformat()},
            conn=conn
        )
        return {"success": True, "case_id": case_id, "status": "REJECTED", "reason": reason}

    def submit_feedback(self, case_id: str, solved: bool, comment: str, conn=None) -> Dict[str, Any]:
        """Feedback handler: if not solved, reopen and escalate to human review."""
        if case_id not in ACTIVE_CASES:
            return {"success": False, "error": f"Case {case_id} not found."}

        case = ACTIVE_CASES[case_id]
        if not solved:
            case.status = "REOPENED_ESCALATED"
            case.case_brief = generate_case_brief(case)
            case.case_brief["reopen_reason"] = f"Customer unsatisfied with automated resolution: {comment}"
            action = "CASE_REOPENED_UNSATISFIED"
        else:
            action = "CUSTOMER_FEEDBACK_SATISFIED"

        self.audit_chain.append_log(
            client_id=case.client_id,
            case_id=case_id,
            action=action,
            payload_data={"solved": solved, "comment": comment, "timestamp": datetime.utcnow().isoformat()},
            conn=conn
        )
        return {"success": True, "case_id": case_id, "status": case.status, "solved": solved}

    def check_approval_timeouts(self, max_wait_hours: float = 24.0, conn=None) -> List[str]:
        """Escalates WAITING_APPROVAL cases that exceed the timeout window."""
        escalated_cases = []
        now = datetime.utcnow()

        for case_id, case in ACTIVE_CASES.items():
            if case.status == "WAITING_APPROVAL":
                created = datetime.fromisoformat(case.created_at)
                if (now - created) > timedelta(hours=max_wait_hours):
                    case.status = "ESCALATED"
                    case.escalation_decision["reasons"].append("APPROVAL_TIMEOUT: Case exceeded maximum supervisor approval window.")
                    case.case_brief = generate_case_brief(case)
                    self.audit_chain.append_log(
                        client_id=case.client_id,
                        case_id=case_id,
                        action="APPROVAL_TIMEOUT_ESCALATED",
                        payload_data={"timeout_hours": max_wait_hours},
                        conn=conn
                    )
                    escalated_cases.append(case_id)
        return escalated_cases

resolution_graph = ResolutionGraph()
