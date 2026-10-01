"""
Resolution Agent for OmniResolve.
Formulates the proposed action, calculates compensation amount based on policy clauses,
and drafts a brand-aligned customer message according to the client's tone guidelines.
"""

from typing import Dict, Any
from engine.types import CaseFile

class ResolutionAgent:
    def formulate_resolution(self, case_file: CaseFile) -> Dict[str, Any]:
        client_id = case_file.client_id
        intent = case_file.intent or {}
        order = case_file.order_details or {}
        customer = case_file.customer_profile or {}
        customer_name = customer.get("name", "Valued Customer")
        order_id = case_file.order_id or "your order"

        action = "REVIEW"
        amount = 0.0
        policy_citation = "General Terms"

        # High-risk security and clinical triggers supersede routine telemetry
        if intent.get("fraud_claim"):
            action = "ESCALATE_TO_FRAUD_SECURITY"
            amount = 0.0
            policy_citation = "Security & Fraud Policy"
            customer_message = (
                f"Dear {customer_name}, we take security claims very seriously. Your dispute has been flagged "
                f"for immediate investigation by our Fraud & Account Security Specialists."
            )

        elif intent.get("medical_mention"):
            action = "ESCALATE_TO_CLINICAL_TRIAGE"
            amount = 0.0
            policy_citation = "CareLink Safety §4.2"
            customer_message = (
                f"Dear {customer_name}, your safety and well-being are our highest priority. Because your message "
                f"mentions medical symptoms or medication, our automated system cannot answer directly. "
                f"We are connecting you immediately with a licensed CareLink clinical triage nurse."
            )

        elif intent.get("legal_threat"):
            action = "ESCALATE_TO_LEGAL_COMPLIANCE"
            amount = 0.0
            policy_citation = "Corporate Compliance Gate"
            customer_message = (
                f"Dear {customer_name}, your case has been transferred directly to our Senior Compliance "
                f"and Executive Relations Department for dedicated handling."
            )

        # Determine action and amount based on diagnostic data
        elif order.get("duplicate_charges_found"):
            amount = float(order.get("duplicate_amount", 0.0))
            if client_id == "carelink":
                action = "REFUND_DUPLICATE_COPAY"
                policy_citation = "CareLink Billing §1.1"
                customer_message = (
                    f"Dear {customer_name}, we verified a duplicate copay charge of ${amount:.2f} "
                    f"for encounter {order_id}. A full refund of ${amount:.2f} has been processed back "
                    f"to your original payment account. Thank you for your patience."
                )
            else:
                action = "REFUND_DUPLICATE_CHARGE"
                policy_citation = f"{client_id.capitalize()} Refund §1.1"
                customer_message = (
                    f"Hi {customer_name}, we confirmed a technical glitch resulted in a duplicate charge "
                    f"of ${amount:.2f} on order {order_id}. We have immediately refunded the extra ${amount:.2f} "
                    f"to your card. You should see it reflected on your statement shortly."
                )

        elif order.get("outage_recorded"):
            amount = 35.00  # TeleNet outage policy flat credit for >36h
            action = "APPLY_OUTAGE_SERVICE_CREDIT"
            policy_citation = "TeleNet Outage §2.2"
            customer_message = (
                f"Dear {customer_name}, our network engineering logs confirm an extended service outage "
                f"affecting your location for order {order_id}. In accordance with TeleNet Outage §2.2, "
                f"we have applied a $35.00 courtesy service credit to your account."
            )

        elif order.get("delivery_gap"):
            amount = 10.00  # QuickCart SLA courtesy credit
            action = "APPLY_SLA_COURTESY_CREDIT"
            policy_citation = "QuickCart Delivery §2.1"
            customer_message = (
                f"Hello {customer_name}, we deeply apologize for the transit delay on order {order_id}. "
                f"Per QuickCart Delivery §2.1, we have credited $10.00 to your account as an apology "
                f"for missing our delivery SLA."
            )

        elif order.get("contradictions"):
            amount = min(50.00, float(order.get("total_amount", 50.00)))
            action = "INVESTIGATE_DELIVERY_DISCREPANCY"
            policy_citation = "Delivery §2.2"
            customer_message = (
                f"Hello {customer_name}, while carrier records show the parcel delivered, we have escalated your "
                f"dispute for supervisor review to initiate a courier tracer or authorize a replacement."
            )

        else:
            action = "GENERAL_CUSTOMER_SERVICE_REVIEW"
            amount = 0.0
            customer_message = (
                f"Thank you for contacting us, {customer_name}. A representative is reviewing your request "
                f"regarding {order_id}."
            )

        resolution = {
            "proposed_action": action,
            "amount": amount,
            "policy_citation": policy_citation,
            "customer_message": customer_message
        }

        case_file.proposed_resolution = resolution
        return resolution

resolution_agent = ResolutionAgent()
