"""
Unit tests for OmniResolve Policy Engine.
Verifies all 6 deterministic safety rules:
1. Wrong client_id (cross-tenant block)
2. Customer not owning the order (ownership block)
3. Refund above amount paid (ledger block)
4. Duplicate refund for same order and reason (duplicate block)
5. Amount above authority limit (returns NEEDS_APPROVAL)
6. Requester approving their own money action (separation of duties block)
"""

import unittest
import sqlite3
import os
from engine.types import RefundRequest, BlockReason
from engine.policy_engine import PolicyEngine
from engine.tools import issue_refund
from db.mock_db import init_db, seed_data

class TestPolicyEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a fresh in-memory or test database
        cls.test_db_path = os.path.join(os.path.dirname(__file__), "test_policy.db")
        cls.conn = init_db(cls.test_db_path)
        seed_data(cls.conn)
        cls.engine = PolicyEngine(limits={
            "quickcart": 50.00,
            "telenet": 40.00,
            "carelink": 60.00
        })

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def test_rule_1_wrong_client_id(self):
        """Cross-tenant block: using quickcart client_id to refund a telenet order."""
        req = RefundRequest(
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="TN-ORD-8903",  # TeleNet order
            amount=20.00,
            reason="Service fee refund",
            requester_id="AGENT-01"
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.block_reason, BlockReason.WRONG_CLIENT_ID)
        self.assertIn("Cross-tenant isolation violation", result.message)

    def test_rule_2_customer_not_owning_order(self):
        """Ownership block: customer attempting to refund another customer's order."""
        req = RefundRequest(
            client_id="quickcart",
            customer_id="QC-CUST-109",  # NOT owner of QC-ORD-8901 (owned by QC-CUST-103)
            order_id="QC-ORD-8901",
            amount=20.00,
            reason="Item return",
            requester_id="AGENT-01"
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.block_reason, BlockReason.CUSTOMER_NOT_ORDER_OWNER)
        self.assertIn("Ownership violation", result.message)

    def test_rule_3_refund_above_amount_paid(self):
        """Ledger block: refund request ($150.00) exceeds total paid ($42.50 captured)."""
        req = RefundRequest(
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            amount=150.00,  # exceeds payments of 42.50 x 2 = 85.00
            reason="Excessive refund request",
            requester_id="AGENT-01",
            approver_id="MGR-99"  # with manager approval to bypass rule 5
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.block_reason, BlockReason.REFUND_EXCEEDS_PAID)
        self.assertIn("exceeds total captured payments", result.message)

    def test_rule_4_duplicate_refund_same_order_and_reason(self):
        """Duplicate block: second refund with identical order and reason is blocked."""
        # First issue an initial refund
        order_id = "QC-ORD-8902"
        cust_id = "QC-CUST-104"
        reason = "Late delivery compensation SLA §2.1"
        
        req1 = RefundRequest(
            client_id="quickcart",
            customer_id=cust_id,
            order_id=order_id,
            amount=10.00,
            reason=reason,
            requester_id="AGENT-01"
        )
        res1 = self.engine.validate_refund(req1, self.conn)
        self.assertTrue(res1.allowed)
        
        # Execute the refund into DB
        issue_refund("quickcart", order_id, 10.00, reason, "AGENT-01", self.conn)

        # Attempt duplicate refund with same reason
        req2 = RefundRequest(
            client_id="quickcart",
            customer_id=cust_id,
            order_id=order_id,
            amount=10.00,
            reason=reason,
            requester_id="AGENT-01"
        )
        res2 = self.engine.validate_refund(req2, self.conn)
        self.assertFalse(res2.allowed)
        self.assertEqual(res2.status, "BLOCKED")
        self.assertEqual(res2.block_reason, BlockReason.DUPLICATE_REFUND)
        self.assertIn("Duplicate refund violation", res2.message)

    def test_rule_5_amount_above_authority_limit_returns_needs_approval(self):
        """Limit check: requesting $48 on TeleNet (limit $40) without approver returns NEEDS_APPROVAL."""
        req = RefundRequest(
            client_id="telenet",
            customer_id="TN-CUST-102",
            order_id="TN-ORD-8903",
            amount=48.00,  # exceeds TeleNet limit of 40.00
            reason="Extended outage compensation",
            requester_id="AGENT-01"
            # approver_id omitted
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "NEEDS_APPROVAL")
        self.assertEqual(result.block_reason, BlockReason.AMOUNT_ABOVE_AUTHORITY_LIMIT)
        self.assertIn("Queued for supervisor approval", result.message)

    def test_rule_6_requester_approving_own_money_action(self):
        """Separation of duties: requester cannot set approver_id to themselves."""
        req = RefundRequest(
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            amount=30.00,
            reason="Partial goodwill adjustment",
            requester_id="SUPERVISOR-42",
            approver_id="SUPERVISOR-42"  # Self-approval!
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.block_reason, BlockReason.SELF_APPROVAL_PROHIBITED)
        self.assertIn("Separation of duties violation", result.message)

    def test_valid_refund_allowed(self):
        """Valid case: within authority limit, legitimate owner, valid amount passes."""
        req = RefundRequest(
            client_id="carelink",
            customer_id="CL-CUST-104",
            order_id="CL-ORD-8904",
            amount=50.00,  # CareLink limit is 60.00
            reason="Duplicate copay billing correction Billing §1.1",
            requester_id="AGENT-01"
        )
        result = self.engine.validate_refund(req, self.conn)
        self.assertTrue(result.allowed)
        self.assertEqual(result.status, "ALLOWED")
        self.assertIsNone(result.block_reason)

if __name__ == "__main__":
    unittest.main()
