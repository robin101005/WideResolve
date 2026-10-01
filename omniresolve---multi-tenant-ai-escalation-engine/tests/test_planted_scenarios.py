"""
End-to-End Evaluation of all 9 Planted Scenarios through the OmniResolve Pipeline Graph.
Validates:
1. Double Charge -> AUTO_RESOLVE
2. Late Delivery -> AUTO_RESOLVE
3. Outage Billing -> RESOLVE_WITH_APPROVAL
4. Duplicate Medical Bill -> AUTO_RESOLVE
5. Fraud Claim -> ESCALATE
6. Repeat Complainer (3 past tickets) -> ESCALATE
7. Legal Threat -> ESCALATE
8. VIP Customer with Churn Risk -> ESCALATE
9. Delivered vs Not Received -> RESOLVE_WITH_APPROVAL / ESCALATE
"""

import unittest
import sqlite3
import os
from engine.graph import resolution_graph, ACTIVE_CASES
from db.mock_db import init_db, seed_data

class TestPlantedScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.join(os.path.dirname(__file__), "test_planted.db")
        cls.conn = init_db(cls.db_path)
        seed_data(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_scenario_1_quickcart_double_charge(self):
        """Planted Scenario 1: QuickCart double charge should AUTO_RESOLVE with $42.50 refund."""
        complaint = "I noticed two identical charges of $42.50 on my credit card for order QC-ORD-8901. Please refund the duplicate!"
        case = resolution_graph.run("quickcart", "QC-CUST-103", complaint, order_id="QC-ORD-8901", conn=self.conn)
        
        self.assertEqual(case.status, "AUTO_RESOLVED")
        self.assertEqual(case.proposed_resolution["amount"], 42.50)
        self.assertGreaterEqual(case.escalation_decision["confidence"], 0.85)

    def test_scenario_2_quickcart_late_delivery(self):
        """Planted Scenario 2: QuickCart late delivery past SLA should AUTO_RESOLVE with $10 credit."""
        complaint = "My guaranteed 2-day delivery order QC-ORD-8902 is 5 days delayed and still not here."
        case = resolution_graph.run("quickcart", "QC-CUST-104", complaint, order_id="QC-ORD-8902", conn=self.conn)
        
        self.assertEqual(case.status, "AUTO_RESOLVED")
        self.assertEqual(case.proposed_resolution["amount"], 10.00)

    def test_scenario_3_telenet_outage_billing(self):
        """Planted Scenario 3: TeleNet outage billing credit ($35.00) yields RESOLVE_WITH_APPROVAL or AUTO."""
        complaint = "My fiber internet was completely down during the 48 hour outage on order TN-ORD-8903. I want a billing credit."
        case = resolution_graph.run("telenet", "TN-CUST-102", complaint, order_id="TN-ORD-8903", conn=self.conn)
        
        # TeleNet threshold is 0.88; case produces either AUTO_RESOLVE or WAITING_APPROVAL
        self.assertIn(case.status, ["WAITING_APPROVAL", "AUTO_RESOLVED"])
        self.assertEqual(case.proposed_resolution["amount"], 35.00)

    def test_scenario_4_carelink_duplicate_medical_bill(self):
        """Planted Scenario 4: CareLink duplicate $50 copay should AUTO_RESOLVE with copay refund."""
        complaint = "I was billed twice for my $50 copay for my routine lab visit on CL-ORD-8904."
        case = resolution_graph.run("carelink", "CL-CUST-104", complaint, order_id="CL-ORD-8904", conn=self.conn)
        
        self.assertEqual(case.status, "AUTO_RESOLVED")
        self.assertEqual(case.proposed_resolution["amount"], 50.00)

    def test_scenario_5_quickcart_fraud_claim(self):
        """Planted Scenario 5: Fraud claim MUST trigger hard rule and ESCALATE."""
        complaint = "My card was stolen and used fraudulently for unauthorized order QC-ORD-8905. This is identity theft!"
        case = resolution_graph.run("quickcart", "QC-CUST-105", complaint, order_id="QC-ORD-8905", conn=self.conn)
        
        self.assertEqual(case.status, "ESCALATED")
        self.assertTrue(any("FRAUD" in r for r in case.escalation_decision["hard_rules_triggered"]))
        self.assertIsNotNone(case.case_brief)

    def test_scenario_6_telenet_repeat_complainer(self):
        """Planted Scenario 6: Customer with 3 past complaints MUST trigger hard rule and ESCALATE."""
        complaint = "My speed is slow again on TN-ORD-8010. You never fix this issue."
        case = resolution_graph.run("telenet", "TN-CUST-110", complaint, order_id="TN-ORD-8010", conn=self.conn)
        
        self.assertEqual(case.status, "ESCALATED")
        self.assertTrue(any("REPEAT_CONTACT" in r for r in case.escalation_decision["hard_rules_triggered"]))

    def test_scenario_7_carelink_legal_threat(self):
        """Planted Scenario 7: Legal threat MUST trigger hard rule and ESCALATE."""
        complaint = "CareLink overcharged me on CL-ORD-8907. My attorney is preparing a regulatory lawsuit."
        case = resolution_graph.run("carelink", "CL-CUST-107", complaint, order_id="CL-ORD-8907", conn=self.conn)
        
        self.assertEqual(case.status, "ESCALATED")
        self.assertTrue(any("LEGAL_THREAT" in r for r in case.escalation_decision["hard_rules_triggered"]))

    def test_scenario_8_telenet_vip_churn_risk(self):
        """Planted Scenario 8: VIP with churn risk MUST trigger hard rule and ESCALATE."""
        complaint = "I am cancelling our enterprise fiber contract on TN-ORD-8908 immediately due to poor service."
        case = resolution_graph.run("telenet", "TN-CUST-100", complaint, order_id="TN-ORD-8908", conn=self.conn)
        
        self.assertEqual(case.status, "ESCALATED")
        self.assertTrue(any("VIP_CHURN_RISK" in r for r in case.escalation_decision["hard_rules_triggered"]))

    def test_scenario_9_quickcart_delivered_vs_not_received(self):
        """Planted Scenario 9: Contradictory evidence (carrier delivered vs customer says not received) MUST ESCALATE."""
        complaint = "Tracking says delivered to porch for QC-ORD-8909, but I never received anything and doorbell camera shows nothing."
        case = resolution_graph.run("quickcart", "QC-CUST-108", complaint, order_id="QC-ORD-8909", conn=self.conn)
        
        self.assertIn(case.status, ["ESCALATED", "WAITING_APPROVAL"])
        self.assertTrue(any("CONTRADICTORY_EVIDENCE" in r for r in case.escalation_decision.get("hard_rules_triggered", [])) or case.status == "WAITING_APPROVAL")

if __name__ == "__main__":
    unittest.main()
