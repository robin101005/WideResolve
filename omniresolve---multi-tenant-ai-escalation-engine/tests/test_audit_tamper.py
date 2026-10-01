"""
Unit test for Hash-Chained Audit Log and Tamper Detection.
Proves that modifying or tampering with any historical row breaks verify_chain().
"""

import unittest
import sqlite3
import os
from engine.audit_chain import AuditChain, GENESIS_HASH
from db.mock_db import init_db

class TestAuditTamper(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(os.path.dirname(__file__), "test_audit_run.db")
        self.conn = init_db(self.test_db)
        self.chain = AuditChain(db_conn_factory=lambda: sqlite3.connect(self.test_db))
        # Seed 5 legitimate entries
        for i in range(1, 6):
            self.chain.append_log(
                client_id="quickcart",
                case_id=f"CASE-{i:03d}",
                action=f"ACTION_{i}",
                payload_data={"step": i, "status": "OK"},
                conn=self.conn
            )

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_unbroken_chain_verifies_successfully(self):
        """Verify unbroken chain with 5 legitimate entries."""
        res = self.chain.verify_chain(self.conn)
        self.assertTrue(res["valid"])
        self.assertEqual(res["total_records"], 5)
        self.assertIn("cryptographic integrity verified", res["message"].lower())

    def test_tampering_breaks_cryptographic_chain(self):
        """Modifying a historical payload directly in the database immediately triggers tamper detection."""
        cursor = self.conn.cursor()
        # Tamper with row #3: change its payload
        cursor.execute("UPDATE audit_log SET payload = '{\"step\": 3, \"hacked\": true}' WHERE id = 3")
        self.conn.commit()

        # Run verification
        res = self.chain.verify_chain(self.conn)
        self.assertFalse(res["valid"])
        self.assertEqual(res["broken_at_id"], 3)
        self.assertEqual(res["error_type"], "HASH_CORRUPTION")
        self.assertIn("Tamper detected", res["message"])

    def test_tampering_with_previous_hash_pointer_breaks_chain(self):
        """Tampering with previous_hash pointer also breaks the chain."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE audit_log SET previous_hash = 'badbeef' WHERE id = 4")
        self.conn.commit()

        res = self.chain.verify_chain(self.conn)
        self.assertFalse(res["valid"])
        self.assertEqual(res["broken_at_id"], 4)
        self.assertEqual(res["error_type"], "PREVIOUS_HASH_MISMATCH")

if __name__ == "__main__":
    unittest.main()
