"""
Unit tests for OmniResolve Escalation Gate.
Proves that every hard rule in plain code always triggers ESCALATE,
and verifies the multi-factor confidence thresholds for AUTO_RESOLVE and RESOLVE_WITH_APPROVAL.
"""

import unittest
from engine.types import CaseFile, EscalationOutcome
from engine.escalation_gate import EscalationGate

class TestEscalationGate(unittest.TestCase):
    def setUp(self):
        self.gate = EscalationGate()

    def test_hard_rule_1_legal_threat_always_escalates(self):
        case = CaseFile(
            case_id="TEST-LEG-01",
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            intent={"legal_threat": True, "fraud_claim": False, "medical_mention": False},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("LEGAL_THREAT" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_2_fraud_claim_always_escalates(self):
        case = CaseFile(
            case_id="TEST-FRD-01",
            client_id="quickcart",
            customer_id="QC-CUST-105",
            order_id="QC-ORD-8905",
            intent={"legal_threat": False, "fraud_claim": True, "medical_mention": False},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("FRAUD_CLAIM" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_3_carelink_medical_mention_always_escalates(self):
        case = CaseFile(
            case_id="TEST-MED-01",
            client_id="carelink",
            customer_id="CL-CUST-104",
            order_id="CL-ORD-8904",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": True},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("CLINICAL_FIREWALL" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_4_amount_above_limit_always_escalates(self):
        case = CaseFile(
            case_id="TEST-AMT-01",
            client_id="quickcart",  # Limit is 50.00
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 95.00},  # Exceeds 50.00
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("AMOUNT_ABOVE_LIMIT" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_5_third_repeat_contact_always_escalates(self):
        case = CaseFile(
            case_id="TEST-RPT-01",
            client_id="telenet",
            customer_id="TN-CUST-110",
            order_id="TN-ORD-8010",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 20.00},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 3, "history_consistency": 0.4},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("REPEAT_CONTACT" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_6_vip_churn_risk_always_escalates(self):
        case = CaseFile(
            case_id="TEST-VIP-01",
            client_id="telenet",
            customer_id="TN-CUST-100",
            order_id="TN-ORD-8908",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 30.00},
            customer_profile={"tier": "VIP", "churn_risk": True, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("VIP_CHURN_RISK" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_7_contradictory_evidence_always_escalates(self):
        case = CaseFile(
            case_id="TEST-CNT-01",
            client_id="quickcart",
            customer_id="QC-CUST-108",
            order_id="QC-ORD-8909",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 25.00},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.8},
            order_details={
                "evidence_agreement": 0.45,
                "contradictions": ["Carrier telemetry claims 'Delivered', but customer reports non-receipt."]
            },
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.40
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("CONTRADICTORY_EVIDENCE" in r for r in decision["hard_rules_triggered"]))

    def test_hard_rule_8_no_matching_policy_always_escalates(self):
        case = CaseFile(
            case_id="TEST-POL-01",
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 20.00},
            customer_profile={"tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[],  # No matching policy
            root_cause_margin=0.85
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.ESCALATE.value)
        self.assertTrue(any("NO_MATCHING_POLICY" in r for r in decision["hard_rules_triggered"]))

    def test_auto_resolve_when_all_guards_pass_and_confidence_high(self):
        """Standard double charge on QuickCart with $42.50 auto-resolves cleanly."""
        case = CaseFile(
            case_id="TEST-AUTO-01",
            client_id="quickcart",
            customer_id="QC-CUST-103",
            order_id="QC-ORD-8901",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 42.50, "policy_citation": "Refund §1.1"},
            customer_profile={"exists": False, "tier": "Standard", "churn_risk": False, "repeat_complaint_count": 0, "history_consistency": 0.9},
            order_details={"evidence_agreement": 0.95, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.45}],
            root_cause_margin=0.82
        )
        # confidence = 0.4*0.95 (0.38) + 0.3*1.0 (0.30) + 0.2*0.82 (0.164) + 0.1*0.90 (0.09) = 0.934 >= 0.85
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.AUTO_RESOLVE.value)
        self.assertGreaterEqual(decision["confidence"], 0.85)

    def test_resolve_with_approval_when_confidence_moderate(self):
        """Moderate confidence case between 0.60 and 0.88 yields RESOLVE_WITH_APPROVAL."""
        case = CaseFile(
            case_id="TEST-APPR-01",
            client_id="telenet",
            customer_id="TN-CUST-102",
            order_id="TN-ORD-8903",
            intent={"legal_threat": False, "fraud_claim": False, "medical_mention": False},
            proposed_resolution={"amount": 35.00, "policy_citation": "Outage §2.2"},
            customer_profile={"exists": False, "tier": "Standard", "churn_risk": False, "repeat_complaint_count": 1, "history_consistency": 0.80},
            order_details={"evidence_agreement": 0.80, "contradictions": []},
            relevant_policies=[{"similarity_score": 0.30}],
            root_cause_margin=0.45
        )
        decision = self.gate.evaluate(case)
        self.assertEqual(decision["outcome"], EscalationOutcome.RESOLVE_WITH_APPROVAL.value)

if __name__ == "__main__":
    unittest.main()
