"""
FastAPI Server for OmniResolve Multi-Tenant Platform.
Exposes endpoints for complaint processing, case management, approvals,
feedback, and cryptographic audit log verification.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from engine.graph import resolution_graph, ACTIVE_CASES
from engine.audit_chain import audit_chain
from engine.tools import get_orders, get_customer, get_db_connection

# Simple dictionary-based or FastAPI router representation
def process_submit_complaint(data: Dict[str, Any]) -> Dict[str, Any]:
    client_id = data.get("client_id", "quickcart").lower()
    customer_id = data.get("customer_id", "")
    raw_complaint = data.get("complaint", "")
    order_id = data.get("order_id")

    case = resolution_graph.run(
        client_id=client_id,
        customer_id=customer_id,
        raw_complaint=raw_complaint,
        order_id=order_id
    )

    return {
        "case_id": case.case_id,
        "client_id": case.client_id,
        "customer_id": case.customer_id,
        "order_id": case.order_id,
        "status": case.status,
        "intent": case.intent,
        "order_details": case.order_details,
        "proposed_resolution": case.proposed_resolution,
        "escalation_decision": case.escalation_decision,
        "case_brief": case.case_brief,
        "created_at": case.created_at
    }

def process_get_case(case_id: str) -> Optional[Dict[str, Any]]:
    case = ACTIVE_CASES.get(case_id)
    if not case:
        return None
    return {
        "case_id": case.case_id,
        "client_id": case.client_id,
        "customer_id": case.customer_id,
        "order_id": case.order_id,
        "status": case.status,
        "raw_complaint": case.raw_complaint,
        "sanitized_complaint": case.sanitized_complaint,
        "intent": case.intent,
        "customer_profile": case.customer_profile,
        "order_details": case.order_details,
        "relevant_policies": case.relevant_policies,
        "root_cause_hypotheses": case.root_cause_hypotheses,
        "root_cause_margin": case.root_cause_margin,
        "proposed_resolution": case.proposed_resolution,
        "escalation_decision": case.escalation_decision,
        "case_brief": case.case_brief,
        "created_at": case.created_at
    }

def process_list_cases(client_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    cases = list(ACTIVE_CASES.values())
    if client_id:
        cases = [c for c in cases if c.client_id == client_id.lower()]
    if status:
        cases = [c for c in cases if c.status == status]
    return [
        {
            "case_id": c.case_id,
            "client_id": c.client_id,
            "customer_id": c.customer_id,
            "order_id": c.order_id,
            "status": c.status,
            "issue_type": c.intent.get("issue_type") if c.intent else "General",
            "amount": c.proposed_resolution.get("amount", 0.0) if c.proposed_resolution else 0.0,
            "confidence": c.escalation_decision.get("confidence", 0.0) if c.escalation_decision else 0.0,
            "created_at": c.created_at
        }
        for c in sorted(cases, key=lambda x: x.created_at, reverse=True)
    ]

def process_approve_case(case_id: str, approver_id: str) -> Dict[str, Any]:
    return resolution_graph.approve_case(case_id, approver_id)

def process_reject_case(case_id: str, rejecter_id: str, reason: str) -> Dict[str, Any]:
    return resolution_graph.reject_case(case_id, rejecter_id, reason)

def process_feedback(case_id: str, solved: bool, comment: str) -> Dict[str, Any]:
    return resolution_graph.submit_feedback(case_id, solved, comment)

def process_verify_audit() -> Dict[str, Any]:
    return audit_chain.verify_chain()

def process_get_audit_logs(client_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if client_id:
            cursor.execute(
                "SELECT * FROM audit_log WHERE client_id = ? ORDER BY id DESC LIMIT ?",
                (client_id.lower(), limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    finally:
        conn.close()
