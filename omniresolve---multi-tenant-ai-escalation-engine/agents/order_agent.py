"""
Order and Transaction Agent for OmniResolve.
Inspects order timeline, payment status, detects duplicate captures, delivery gaps,
and flags contradictions between system records and customer claims.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from engine.tools import get_orders, get_payments
from engine.types import CaseFile

class OrderTransactionAgent:
    def analyze(self, case_file: CaseFile, conn=None) -> Dict[str, Any]:
        client_id = case_file.client_id
        order_id = case_file.order_id
        customer_id = case_file.customer_id

        if not order_id:
            # Try to infer order from customer's most recent order
            cust_orders = get_orders(client_id, customer_id=customer_id, conn=conn)
            if cust_orders:
                order_id = cust_orders[0]["id"]
                case_file.order_id = order_id

        orders = get_orders(client_id, order_id=order_id, conn=conn) if order_id else []
        payments = get_payments(client_id, order_id, conn=conn) if order_id else []

        if not orders:
            order_summary = {
                "order_found": False,
                "order_id": order_id,
                "contradictions": ["Order not found in client database"],
                "evidence_agreement": 0.20,
                "duplicate_charges_found": False
            }
            case_file.order_details = order_summary
            return order_summary

        order = orders[0]
        total_amount = float(order.get("total_amount", 0.0))
        carrier_status = order.get("carrier_status", "")
        delivery_notes = order.get("delivery_notes", "")
        order_status = order.get("status", "")

        # 1. Timeline & Duplicate Charges Check
        captured_payments = [p for p in payments if p.get("status") == "Captured"]
        duplicate_charges = False
        duplicate_amount = 0.0
        
        if len(captured_payments) > 1:
            # Check if there are identical amounts captured close together
            amounts = [float(p["amount"]) for p in captured_payments]
            for amt in set(amounts):
                if amounts.count(amt) > 1:
                    duplicate_charges = True
                    duplicate_amount = amt
                    break

        # 2. Check Contradictions Between Systems
        contradictions: List[str] = []
        raw_complaint_lower = case_file.raw_complaint.lower()

        # Carrier says delivered, but customer complains they never received it
        if "delivered" in carrier_status.lower() and ("not received" in raw_complaint_lower or "never got" in raw_complaint_lower or "missing" in raw_complaint_lower):
            contradictions.append(
                f"Carrier discrepancy: Carrier telemetry claims '{carrier_status}', but customer reports non-receipt."
            )

        # Order marked delayed in system vs customer late complaint
        delivery_gap = False
        if "delayed" in order_status.lower() or "delayed" in carrier_status.lower():
            delivery_gap = True

        # Outage recorded in telemetry
        outage_recorded = "outage" in order_status.lower() or "outage" in carrier_status.lower() or "outage" in delivery_notes.lower()

        # Evidence agreement scoring
        if contradictions:
            evidence_agreement = 0.45  # Contradictory evidence
        elif duplicate_charges:
            evidence_agreement = 1.0  # Indisputable mathematical proof in payment ledger
        elif delivery_gap or outage_recorded:
            evidence_agreement = 0.95  # Telemetry confirms customer's exact issue!
        else:
            evidence_agreement = 0.80

        order_summary = {
            "order_found": True,
            "order_id": order_id,
            "order_date": order.get("order_date"),
            "order_status": order_status,
            "total_amount": total_amount,
            "carrier_status": carrier_status,
            "delivery_notes": delivery_notes,
            "payment_count": len(captured_payments),
            "captured_total": sum(float(p["amount"]) for p in captured_payments),
            "duplicate_charges_found": duplicate_charges,
            "duplicate_amount": duplicate_amount,
            "delivery_gap": delivery_gap,
            "outage_recorded": outage_recorded,
            "contradictions": contradictions,
            "evidence_agreement": evidence_agreement
        }

        case_file.order_details = order_summary
        return order_summary

order_agent = OrderTransactionAgent()
