"""
Customer History Agent for OmniResolve.
Analyzes account standing, tier, lifetime value (LTV), repeat complaints, and past tickets.
"""

from typing import Dict, Any, Optional
from engine.tools import get_customer, get_past_tickets
from engine.types import CaseFile

class CustomerHistoryAgent:
    def analyze(self, case_file: CaseFile, conn=None) -> Dict[str, Any]:
        client_id = case_file.client_id
        customer_id = case_file.customer_id

        customer = get_customer(client_id, customer_id, conn=conn)
        past_tickets = get_past_tickets(client_id, customer_id, conn=conn)

        if not customer:
            profile = {
                "exists": False,
                "tier": "Unknown",
                "ltv": 0.0,
                "churn_risk": False,
                "repeat_complaint_count": 0,
                "past_ticket_count": 0,
                "history_consistency": 0.5
            }
        else:
            tier = customer.get("tier", "Standard")
            ltv = float(customer.get("ltv", 0.0))
            raw_text = case_file.raw_complaint.lower()
            intent_churn = "cancel" in raw_text or "terminat" in raw_text or "leaving" in raw_text
            churn_risk = bool(customer.get("churn_risk", 0)) or intent_churn
            repeat_count = int(customer.get("repeat_complaint_count", 0))
            past_ticket_count = len(past_tickets)

            # Measure consistency: regular good standing customers have high consistency
            if repeat_count >= 3 or past_ticket_count >= 3:
                history_consistency = 0.35  # Frequent complainer
            else:
                history_consistency = 0.95

            profile = {
                "exists": True,
                "name": customer.get("name"),
                "tier": tier,
                "ltv": ltv,
                "churn_risk": churn_risk,
                "repeat_complaint_count": max(repeat_count, past_ticket_count),
                "past_ticket_count": past_ticket_count,
                "past_tickets_summary": [
                    {"id": t["id"], "issue": t["issue_type"], "sentiment": t["sentiment"]}
                    for t in past_tickets[:3]
                ],
                "history_consistency": history_consistency
            }

        case_file.customer_profile = profile
        return profile

history_agent = CustomerHistoryAgent()
