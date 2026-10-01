"""
Cryptographic Hash-Chained Audit Log and Case Brief Generator for OmniResolve.
Each audit row stores sha256(previous_hash + timestamp + case_id + action + payload).
Provides tamper-detection validation and comprehensive case brief generation.
"""

import hashlib
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from engine.tools import get_db_connection

GENESIS_HASH = "0" * 64

class AuditChain:
    def __init__(self, db_conn_factory=get_db_connection):
        self.get_conn = db_conn_factory

    @staticmethod
    def compute_hash(previous_hash: str, timestamp: str, case_id: str, action: str, payload: str) -> str:
        """sha256(previous_hash + timestamp + case_id + action + payload)"""
        raw = f"{previous_hash}{timestamp}{case_id}{action}{payload}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def append_log(
        self,
        client_id: str,
        case_id: str,
        action: str,
        payload_data: Any,
        conn: Optional[sqlite3.Connection] = None
    ) -> Dict[str, Any]:
        """Appends a new immutable, hash-linked log entry into the audit_log table."""
        close_conn = False
        if conn is None:
            conn = self.get_conn()
            close_conn = True

        try:
            cursor = conn.cursor()
            # Fetch the most recent hash for this chain
            cursor.execute("SELECT current_hash FROM audit_log ORDER BY id DESC LIMIT 1")
            last_row = cursor.fetchone()
            previous_hash = last_row[0] if last_row else GENESIS_HASH

            now_str = datetime.utcnow().isoformat()
            payload_str = json.dumps(payload_data, sort_keys=True) if not isinstance(payload_data, str) else payload_data
            current_hash = self.compute_hash(previous_hash, now_str, case_id, action, payload_str)

            cursor.execute("""
            INSERT INTO audit_log (client_id, case_id, timestamp, action, payload, previous_hash, current_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (client_id.lower(), case_id, now_str, action, payload_str, previous_hash, current_hash))

            conn.commit()

            return {
                "id": cursor.lastrowid,
                "client_id": client_id.lower(),
                "case_id": case_id,
                "timestamp": now_str,
                "action": action,
                "payload": payload_str,
                "previous_hash": previous_hash,
                "current_hash": current_hash
            }
        finally:
            if close_conn:
                conn.close()

    def verify_chain(self, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
        """
        Walks the entire audit log from row 1 to N, recomputing and verifying the cryptographic hash chain.
        Detects any tampering, deletion, or modification.
        """
        close_conn = False
        if conn is None:
            conn = self.get_conn()
            close_conn = True

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, client_id, case_id, timestamp, action, payload, previous_hash, current_hash FROM audit_log ORDER BY id ASC")
            rows = cursor.fetchall()

            if not rows:
                return {
                    "valid": True,
                    "total_records": 0,
                    "message": "Audit chain is empty. Genesis state intact."
                }

            expected_prev_hash = GENESIS_HASH
            for idx, row in enumerate(rows):
                cols = [c[0] for c in cursor.description]
                r = dict(zip(cols, row))
                row_id = r["id"]

                # 1. Verify previous hash pointer
                if r["previous_hash"] != expected_prev_hash:
                    return {
                        "valid": False,
                        "broken_at_id": row_id,
                        "index": idx,
                        "error_type": "PREVIOUS_HASH_MISMATCH",
                        "expected_previous_hash": expected_prev_hash,
                        "stored_previous_hash": r["previous_hash"],
                        "message": f"Tamper detected at row #{row_id}: previous_hash does not match preceding record."
                    }

                # 2. Recompute current hash
                recomputed = self.compute_hash(
                    r["previous_hash"],
                    r["timestamp"],
                    r["case_id"],
                    r["action"],
                    r["payload"]
                )

                if recomputed != r["current_hash"]:
                    return {
                        "valid": False,
                        "broken_at_id": row_id,
                        "index": idx,
                        "error_type": "HASH_CORRUPTION",
                        "expected_hash": recomputed,
                        "stored_hash": r["current_hash"],
                        "message": f"Tamper detected at row #{row_id}: data payload or metadata was altered."
                    }

                expected_prev_hash = r["current_hash"]

            return {
                "valid": True,
                "total_records": len(rows),
                "last_hash": expected_prev_hash,
                "message": f"Cryptographic integrity verified: all {len(rows)} audit records intact with unbroken SHA-256 chain."
            }
        finally:
            if close_conn:
                conn.close()

def generate_case_brief(case_file) -> Dict[str, Any]:
    """Generates structured Case Brief for human agents when cases are escalated or need approval."""
    client_id = case_file.client_id
    intent = case_file.intent or {}
    customer = case_file.customer_profile or {}
    order = case_file.order_details or {}
    resolution = case_file.proposed_resolution or {}
    decision = case_file.escalation_decision or {}

    summary = (
        f"Complaint filed for {client_id.upper()} account regarding {intent.get('issue_type', 'General Dispute')}. "
        f"Customer sentiment classified as {intent.get('sentiment', 'Neutral')} with {intent.get('urgency', 'Medium')} urgency. "
        f"Order reference: {case_file.order_id or 'None'}. Claim involves ${resolution.get('amount', 0.0):.2f}."
    )

    evidence_timeline = [
        f"1. Customer complaint received: \"{case_file.raw_complaint[:120]}...\"",
        f"2. PII Sanitization executed; sensitive tokens masked.",
        f"3. Account Verification: {customer.get('tier', 'Standard')} Tier | LTV ${customer.get('ltv', 0):.2f} | {customer.get('past_ticket_count', 0)} prior tickets.",
        f"4. Telemetry Inspection: Order Status '{order.get('order_status', 'N/A')}' | Carrier Status '{order.get('carrier_status', 'N/A')}'.",
        f"5. Financial Ledger: {order.get('payment_count', 0)} payment records totaling ${order.get('captured_total', 0):.2f} captured."
    ]

    if order.get("duplicate_charges_found"):
        evidence_timeline.append(f"6. Gateway Glitch Confirmed: Duplicate charge of ${order.get('duplicate_amount', 0):.2f} verified in payments table.")
    if order.get("contradictions"):
        evidence_timeline.append(f"6. System Contradiction: {'; '.join(order.get('contradictions', []))}")

    policy_citations = [
        f"{p.get('citation')} (Similarity: {p.get('similarity_score', 0):.2f}) - {p.get('text', '')[:100]}..."
        for p in (case_file.relevant_policies or [])[:2]
    ]

    recommended_action = {
        "action": resolution.get("proposed_action", "MANUAL_REVIEW"),
        "amount": resolution.get("amount", 0.0),
        "suggested_message": resolution.get("customer_message", "")
    }

    why_escalated = decision.get("reasons", ["Ambiguity or policy threshold requires human verification"])

    return {
        "case_id": case_file.case_id,
        "client_id": client_id,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "evidence_timeline": evidence_timeline,
        "policy_citations": policy_citations,
        "recommended_action": recommended_action,
        "why_escalated": why_escalated,
        "confidence_score": decision.get("confidence", 0.0),
        "hard_rules_triggered": decision.get("hard_rules_triggered", [])
    }

audit_chain = AuditChain()
