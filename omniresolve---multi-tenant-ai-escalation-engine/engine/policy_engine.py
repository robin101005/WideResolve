"""
Deterministic Policy Engine for OmniResolve.
Runs before every financial action tool and strictly enforces 6 security and policy block rules:
1. Wrong client_id (cross-tenant attempt)
2. Customer not owning the order
3. Refund above amount paid (ledger check)
4. Duplicate refund for the same order and reason
5. Amount above authority limit (returns NEEDS_APPROVAL)
6. Requester approving their own money action (separation of duties)
"""

import sqlite3
import os
from typing import Dict, Any, Optional
from engine.types import RefundRequest, PolicyValidationResult, BlockReason
from engine.tools import get_db_connection

# Default authority limits per client
CLIENT_AUTHORITY_LIMITS: Dict[str, float] = {
    "quickcart": 50.00,
    "telenet": 40.00,
    "carelink": 60.00
}

class PolicyEngine:
    def __init__(self, limits: Optional[Dict[str, float]] = None):
        self.limits = limits or CLIENT_AUTHORITY_LIMITS

    def validate_refund(
        self,
        request: RefundRequest,
        conn: Optional[sqlite3.Connection] = None
    ) -> PolicyValidationResult:
        """
        Validates a refund request against all 6 deterministic safety rules.
        """
        request.validate()
        client_id = request.client_id.lower()
        authority_limit = self.limits.get(client_id, 50.00)

        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        try:
            cursor = conn.cursor()

            # Rule 6: Requester approving their own money action (separation of duties)
            # If an explicit approver is specified and matches the requester, reject self-approval
            if request.approver_id and request.approver_id == request.requester_id:
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.SELF_APPROVAL_PROHIBITED,
                    message="Separation of duties violation: requester cannot approve their own financial action.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # Rule 5: Amount above client authority limit
            # Autonomous agent cannot issue amounts exceeding its authority limit without supervisor approval
            if request.amount > authority_limit and not request.approver_id:
                return PolicyValidationResult(
                    allowed=False,
                    status="NEEDS_APPROVAL",
                    block_reason=BlockReason.AMOUNT_ABOVE_AUTHORITY_LIMIT,
                    message=f"Requested amount ${request.amount:.2f} exceeds automated authority limit of ${authority_limit:.2f}. Queued for supervisor approval.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # Rule 1 & Order Lookup: Check if order exists in the requested client_id
            cursor.execute(
                "SELECT * FROM orders WHERE id = ?",
                (request.order_id,)
            )
            order_row = cursor.fetchone()

            if not order_row:
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.UNKNOWN_ORDER,
                    message=f"Order {request.order_id} does not exist.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            cols = [col[0] for col in cursor.description]
            order_data = dict(zip(cols, order_row))

            # Cross-tenant check: Order belongs to a different client
            if order_data["client_id"].lower() != client_id:
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.WRONG_CLIENT_ID,
                    message=f"Cross-tenant isolation violation: Order {request.order_id} belongs to '{order_data['client_id']}', not '{client_id}'.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # Rule 2: Customer not owning the order
            if order_data["customer_id"] != request.customer_id:
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.CUSTOMER_NOT_ORDER_OWNER,
                    message=f"Ownership violation: Customer '{request.customer_id}' does not own order '{request.order_id}' (owned by '{order_data['customer_id']}').",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # Rule 3: Refund above amount paid (ledger check)
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0.0) FROM payments WHERE client_id = ? AND order_id = ? AND status = 'Captured'",
                (client_id, request.order_id)
            )
            total_captured = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0.0) FROM refunds WHERE client_id = ? AND order_id = ? AND status = 'Completed'",
                (client_id, request.order_id)
            )
            total_already_refunded = cursor.fetchone()[0]

            if (total_already_refunded + request.amount) > (total_captured + 0.001):
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.REFUND_EXCEEDS_PAID,
                    message=f"Financial policy violation: Requested refund ${request.amount:.2f} + prior refunds ${total_already_refunded:.2f} exceeds total captured payments of ${total_captured:.2f}.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # Rule 4: Duplicate refund for the same order and reason
            cursor.execute(
                "SELECT count(*) FROM refunds WHERE client_id = ? AND order_id = ? AND reason = ? AND status = 'Completed'",
                (client_id, request.order_id, request.reason)
            )
            duplicate_count = cursor.fetchone()[0]
            if duplicate_count > 0:
                return PolicyValidationResult(
                    allowed=False,
                    status="BLOCKED",
                    block_reason=BlockReason.DUPLICATE_REFUND,
                    message=f"Duplicate refund violation: A completed refund for order '{request.order_id}' with reason '{request.reason}' already exists.",
                    client_id=client_id,
                    order_id=request.order_id,
                    requested_amount=request.amount,
                    authority_limit=authority_limit
                )

            # All 6 checks passed
            return PolicyValidationResult(
                allowed=True,
                status="ALLOWED",
                message="Policy validation successful: All financial, tenancy, and ownership guards satisfied.",
                client_id=client_id,
                order_id=request.order_id,
                requested_amount=request.amount,
                authority_limit=authority_limit
            )

        finally:
            if close_conn:
                conn.close()
