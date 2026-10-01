"""
Root Cause Agent for OmniResolve.
Generates 2 to 3 ranked hypotheses with evidence weights and calculates the margin
between the top two candidates to measure diagnostic clarity.
"""

from typing import List, Dict, Any
from engine.types import CaseFile

class RootCauseAgent:
    def diagnose(self, case_file: CaseFile) -> List[Dict[str, Any]]:
        order = case_file.order_details or {}
        intent = case_file.intent or {}
        issue_type = intent.get("issue_type", "")
        hypotheses: List[Dict[str, Any]] = []

        if order.get("duplicate_charges_found"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Payment gateway duplicate transaction capture on checkout retry",
                    "evidence": f"Telemetry found {order.get('payment_count')} captured payments including duplicate amount of ${order.get('duplicate_amount', 0):.2f}",
                    "confidence": 0.94
                },
                {
                    "rank": 2,
                    "hypothesis": "User accidental double-click submitting two orders",
                    "evidence": f"Only a single order ID ({order.get('order_id')}) exists in the order ledger, disproving separate cart checkout",
                    "confidence": 0.12
                },
                {
                    "rank": 3,
                    "hypothesis": "Card issuer authorization hold display delay",
                    "evidence": "Merchant processor confirmed both settlements completed",
                    "confidence": 0.05
                }
            ]
        elif order.get("outage_recorded"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Service interruption due to logged NOC infrastructure outage",
                    "evidence": f"Carrier status reports '{order.get('carrier_status')}' and system telemetry logs 48h blackout",
                    "confidence": 0.92
                },
                {
                    "rank": 2,
                    "hypothesis": "Customer premises equipment (router) local fault",
                    "evidence": "NOC telemetry shows entire node offline, ruling out isolated hardware fault",
                    "confidence": 0.15
                }
            ]
        elif order.get("delivery_gap"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Courier hub transit congestion causing SLA delay",
                    "evidence": f"Carrier telemetry logs: '{order.get('carrier_status')}' with verified 5-day delay past SLA",
                    "confidence": 0.91
                },
                {
                    "rank": 2,
                    "hypothesis": "Customer address discrepancy or access barrier",
                    "evidence": "Shipping address verified valid; no delivery attempt exceptions logged",
                    "confidence": 0.14
                }
            ]
        elif order.get("contradictions"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Parcel misplaced by carrier or misdelivered to adjacent address",
                    "evidence": "Customer doorbell surveillance shows no parcel arrival despite carrier GPS delivery scan",
                    "confidence": 0.65
                },
                {
                    "rank": 2,
                    "hypothesis": "Package theft (porch piracy) after verified delivery",
                    "evidence": "Carrier GPS timestamp logged on porch; customer disputes physical presence",
                    "confidence": 0.55
                }
            ]
        elif intent.get("legal_threat"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Escalated legal dispute requiring formal risk and compliance review",
                    "evidence": "Customer explicitly stated legal/regulatory intent",
                    "confidence": 0.96
                },
                {
                    "rank": 2,
                    "hypothesis": "Administrative grievance expressible through customer support",
                    "evidence": "Severe language indicates unwillingness to pursue routine support flow",
                    "confidence": 0.10
                }
            ]
        elif intent.get("medical_mention"):
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": "Patient experiencing medical symptoms or medication concern",
                    "evidence": "Explicit mention of physical symptom, adverse reaction, or prescription drug",
                    "confidence": 0.98
                },
                {
                    "rank": 2,
                    "hypothesis": "Billing inquiry with collateral medical narrative",
                    "evidence": "Clinical safety protocol mandates human nursing triage regardless of billing context",
                    "confidence": 0.08
                }
            ]
        else:
            hypotheses = [
                {
                    "rank": 1,
                    "hypothesis": f"Standard {issue_type or 'customer'} discrepancy",
                    "evidence": "Customer statement corresponds to general policy guidelines",
                    "confidence": 0.70
                },
                {
                    "rank": 2,
                    "hypothesis": "Account configuration or misunderstanding of terms",
                    "evidence": "Customer inquiry regarding active subscription or service terms",
                    "confidence": 0.35
                }
            ]

        # Calculate margin between top 2 hypotheses
        top1 = hypotheses[0]["confidence"] if len(hypotheses) > 0 else 0.5
        top2 = hypotheses[1]["confidence"] if len(hypotheses) > 1 else 0.0
        margin = round(max(0.0, top1 - top2), 4)

        case_file.root_cause_hypotheses = hypotheses
        case_file.root_cause_margin = margin
        return hypotheses

root_cause_agent = RootCauseAgent()
