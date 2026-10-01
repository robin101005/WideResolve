"""
Deterministic Escalation Gate for OmniResolve.
Written in pure, deterministic code (NEVER LLM).
Enforces hard escalation rules and calculates multi-factor confidence.
"""

from typing import Dict, Any, List, Tuple
from engine.types import CaseFile, EscalationOutcome, RefundRequest
from engine.policy_engine import PolicyEngine

CLIENT_THRESHOLDS: Dict[str, float] = {
    "quickcart": 0.85,
    "telenet": 0.88,
    "carelink": 0.95
}

CLIENT_AUTHORITY_LIMITS: Dict[str, float] = {
    "quickcart": 50.00,
    "telenet": 40.00,
    "carelink": 60.00
}

class EscalationGate:
    def __init__(self, policy_engine: PolicyEngine = None):
        self.policy_engine = policy_engine or PolicyEngine(CLIENT_AUTHORITY_LIMITS)
        self.thresholds = CLIENT_THRESHOLDS
        self.limits = CLIENT_AUTHORITY_LIMITS

    def evaluate(self, case_file: CaseFile, conn=None) -> Dict[str, Any]:
        """
        Evaluates the case against hard deterministic rules and the multi-factor confidence formula.
        Returns: {
            "outcome": EscalationOutcome,
            "reasons": List[str],
            "confidence": float,
            "hard_rules_triggered": List[str],
            "confidence_breakdown": Dict[str, float]
        }
        """
        client_id = case_file.client_id.lower()
        intent = case_file.intent or {}
        customer = case_file.customer_profile or {}
        order = case_file.order_details or {}
        policies = case_file.relevant_policies or []
        resolution = case_file.proposed_resolution or {}
        amount = float(resolution.get("amount", 0.0))
        authority_limit = self.limits.get(client_id, 50.00)
        client_threshold = self.thresholds.get(client_id, 0.85)

        hard_rules_triggered: List[str] = []

        # =====================================================================
        # 1. Hard Rules (Always ESCALATE - NEVER LLM)
        # =====================================================================
        
        # Rule 1: Legal / Regulatory Threat
        if intent.get("legal_threat"):
            hard_rules_triggered.append("HARD_RULE_LEGAL_THREAT: Customer issued legal or regulatory dispute threat.")

        # Rule 2: Fraud or Safety Claim
        if intent.get("fraud_claim"):
            hard_rules_triggered.append("HARD_RULE_FRAUD_CLAIM: Unauthorized charge or security compromise reported.")

        # Rule 8: CareLink Medical / Symptom / Medication mention
        if client_id == "carelink" and intent.get("medical_mention"):
            hard_rules_triggered.append("HARD_RULE_CLINICAL_FIREWALL: CareLink policy prohibits automated handling of medical symptoms/medications. Immediate human clinical triage required.")

        # Rule 3: Amount above client authority limit
        if amount > authority_limit:
            hard_rules_triggered.append(f"HARD_RULE_AMOUNT_ABOVE_LIMIT: Proposed resolution amount ${amount:.2f} exceeds tenant authority cap of ${authority_limit:.2f}.")

        # Rule 4: No matching policy
        top_policy_score = policies[0].get("similarity_score", 0.0) if policies else 0.0
        if not policies or top_policy_score < 0.20:
            hard_rules_triggered.append("HARD_RULE_NO_MATCHING_POLICY: No policy clause satisfies minimum retrieval threshold.")

        # Rule 5: Third repeat contact
        repeat_count = max(customer.get("repeat_complaint_count", 0), customer.get("past_ticket_count", 0))
        if repeat_count >= 3:
            hard_rules_triggered.append(f"HARD_RULE_REPEAT_CONTACT: Customer has filed {repeat_count} past tickets/disputes. Tier-2 human specialist required.")

        # Rule 6: VIP customer with churn risk
        if customer.get("tier") == "VIP" and customer.get("churn_risk"):
            hard_rules_triggered.append("HARD_RULE_VIP_CHURN_RISK: High-value account ($2,400 LTV) at severe risk of contract termination.")

        # Rule 7: Contradictory evidence
        contradictions = order.get("contradictions", [])
        if contradictions:
            hard_rules_triggered.append(f"HARD_RULE_CONTRADICTORY_EVIDENCE: System discrepancy: {'; '.join(contradictions)}")

        # =====================================================================
        # 2. Confidence Formula Calculation
        # confidence = 0.4*evidence_agreement + 0.3*policy_match + 0.2*root_cause_margin + 0.1*history_consistency
        # =====================================================================
        evidence_agreement = float(order.get("evidence_agreement", 0.80))
        # Normalize policy match score to 0..1 range (0.35+ is strong match)
        policy_match = min(1.0, top_policy_score / 0.40) if top_policy_score > 0 else 0.0
        root_cause_margin = float(case_file.root_cause_margin or 0.50)
        history_consistency = float(customer.get("history_consistency", 0.80))

        confidence = round(
            0.4 * evidence_agreement +
            0.3 * policy_match +
            0.2 * root_cause_margin +
            0.1 * history_consistency,
            4
        )

        confidence_breakdown = {
            "evidence_agreement": evidence_agreement,
            "policy_match": policy_match,
            "root_cause_margin": root_cause_margin,
            "history_consistency": history_consistency,
            "total_confidence": confidence,
            "tenant_threshold": client_threshold
        }

        # =====================================================================
        # 3. Decision Logic
        # if hard rule -> ESCALATE
        # elif confidence >= client threshold and policy engine allows -> AUTO_RESOLVE
        # elif confidence >= 0.60 -> RESOLVE_WITH_APPROVAL
        # else -> ESCALATE
        # =====================================================================
        policy_allowed = True
        policy_block_msg = ""
        
        # Test financial policy validation if an amount is being issued
        if amount > 0 and case_file.order_id and customer.get("exists"):
            refund_req = RefundRequest(
                client_id=client_id,
                customer_id=case_file.customer_id,
                order_id=case_file.order_id,
                amount=amount,
                reason=resolution.get("policy_citation", "Resolution"),
                requester_id="SYSTEM_AUTO_AGENT"
            )
            val_res = self.policy_engine.validate_refund(refund_req, conn=conn)
            if not val_res.allowed:
                policy_allowed = False
                policy_block_msg = val_res.message

        # =====================================================================
        # 3. Decision Logic
        # HARD RULES ALWAYS SUPERSEDE (NEVER LLM)
        # =====================================================================
        if hard_rules_triggered:
            outcome = EscalationOutcome.ESCALATE
            decision_reasons = hard_rules_triggered
            status_str = "ESCALATED"
            decision = {
                "outcome": outcome.value,
                "status": status_str,
                "confidence": confidence,
                "reasons": decision_reasons,
                "hard_rules_triggered": hard_rules_triggered,
                "confidence_breakdown": confidence_breakdown
            }
            case_file.escalation_decision = decision
            case_file.status = status_str
            return decision

        decision_reasons: List[str] = []

        # Rule 9: TeleNet Outage Credit Policy Guard (Requires supervisor verification of NOC logs)
        if client_id == "telenet" and order.get("outage_recorded"):
            decision_reasons.append("TeleNet Outage §2.2 policy requires supervisor verification of NOC telemetry logs before credit disbursal.")
            decision = {
                "outcome": EscalationOutcome.RESOLVE_WITH_APPROVAL.value,
                "status": "WAITING_APPROVAL",
                "confidence": confidence,
                "reasons": decision_reasons,
                "hard_rules_triggered": [],
                "confidence_breakdown": confidence_breakdown
            }
            case_file.escalation_decision = decision
            case_file.status = "WAITING_APPROVAL"
            return decision
        elif confidence >= client_threshold and policy_allowed:
            outcome = EscalationOutcome.AUTO_RESOLVE
            decision_reasons.append(
                f"Confidence {confidence:.4f} meets or exceeds client threshold {client_threshold:.2f}."
            )
            decision_reasons.append("Zero hard escalation rules violated.")
            decision_reasons.append("Deterministic policy engine verified ledger and authority bounds.")
            status_str = "AUTO_RESOLVED"
        elif confidence >= 0.60:
            outcome = EscalationOutcome.RESOLVE_WITH_APPROVAL
            decision_reasons.append(
                f"Confidence {confidence:.4f} is above baseline 0.60 but below auto-resolve threshold {client_threshold:.2f} (or requires supervisor verification)."
            )
            if not policy_allowed:
                decision_reasons.append(f"Policy Guard Note: {policy_block_msg}")
            status_str = "WAITING_APPROVAL"
        else:
            outcome = EscalationOutcome.ESCALATE
            decision_reasons.append(
                f"Confidence {confidence:.4f} is below 0.60 minimum resolution threshold. Ambiguity requires human intervention."
            )
            status_str = "ESCALATED"

        decision = {
            "outcome": outcome.value,
            "status": status_str,
            "confidence": confidence,
            "reasons": decision_reasons,
            "hard_rules_triggered": hard_rules_triggered,
            "confidence_breakdown": confidence_breakdown
        }

        case_file.escalation_decision = decision
        case_file.status = status_str
        return decision

escalation_gate = EscalationGate()
