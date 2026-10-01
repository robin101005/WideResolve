"""
Intent Classification Agent for OmniResolve.
Extracts structured intent, sentiment, urgency, threat flags, and entities.
Treats complaint as untrusted input.
"""

import re
from typing import Dict, Any
from agents.pii_sanitizer import sanitize_pii

# Keywords for deterministic detection
LEGAL_KEYWORDS = [
    "lawyer", "attorney", "lawsuit", "legal action", "court", "litigation",
    "sue you", "regulatory", "fcc", "ftc", "hipaa violation", "counsel", "retain counsel",
    "malpractice", "licensing board", "state attorney"
]

FRAUD_KEYWORDS = [
    "fraud", "stolen", "unauthorized", "identity theft", "scam", "compromised",
    "chargeback", "hacked", "police report", "sim swap"
]

INJECTION_KEYWORDS = [
    "ignore all previous", "ignore previous", "system override", "admin debug",
    "disregard", "forget hospital rules", "forget rules", "you are now in",
    "jailbreak", "developer mode", "prompt injection", "unconditional disbursement"
]

MEDICAL_KEYWORDS = [
    "chest pain", "pain", "swelling", "doctor", "medicine", "medication", "pill", "pills",
    "dosage", "prescription", "allergic", "reaction", "hospital", "emergency",
    "symptom", "side effect", "blood pressure", "clinic advice", "fever", "nausea",
    "vomit", "vomited", "blood", "cough", "coughing", "ingested", "cleaner", "poison",
    "vision", "vision loss", "numbness", "arm", "breathing", "hives", "heart",
    "dizziness", "choking", "dose", "amoxicillin", "nurse", "patient", "clinical"
]

class IntentAgent:
    def parse_intent(self, raw_text: str, client_id: str) -> Dict[str, Any]:
        """
        Extracts structured intent from untrusted text after PII masking.
        """
        sanitized = sanitize_pii(raw_text)
        lower_text = sanitized.lower()

        # 1. Threat & safety checks
        prompt_injection = any(kw in lower_text for kw in INJECTION_KEYWORDS)
        legal_threat = any(kw in lower_text for kw in LEGAL_KEYWORDS)
        fraud_claim = any(kw in lower_text for kw in FRAUD_KEYWORDS)
        medical_mention = any(kw in lower_text for kw in MEDICAL_KEYWORDS)

        if prompt_injection:
            fraud_claim = True  # Treat adversarial injection as critical security threat

        # 2. Extract Entities
        entities: Dict[str, Any] = {}
        # Order ID regex: e.g. QC-ORD-8901, TN-ORD-8903, CL-ORD-8904, or order #8901
        order_match = re.search(r'\b([A-Z]{2}-ORD-\d{4,5})\b', raw_text, re.IGNORECASE)
        if order_match:
            entities["order_id"] = order_match.group(1).upper()
        else:
            simple_order = re.search(r'order\s*(?:#|id|number)?\s*(\d{4,5})', raw_text, re.IGNORECASE)
            if simple_order:
                prefix = client_id[:2].upper()
                entities["order_id"] = f"{prefix}-ORD-{simple_order.group(1)}"

        # Amount regex: e.g. $42.50, $89.99, 50 dollars
        amount_match = re.search(r'\$\s*(\d+(?:\.\d{1,2})?)', raw_text)
        if amount_match:
            entities["amount"] = float(amount_match.group(1))

        # 3. Classify Issue Type
        if "double" in lower_text or "charged twice" in lower_text or "two times" in lower_text or "duplicate" in lower_text:
            if client_id == "carelink":
                issue_type = "Duplicate Medical Copay"
            else:
                issue_type = "Double Charge"
        elif "outage" in lower_text or "blackout" in lower_text or "down for" in lower_text:
            issue_type = "Outage Billing"
        elif "delayed" in lower_text or "late" in lower_text or "past delivery" in lower_text:
            issue_type = "Late Delivery"
        elif "delivered" in lower_text and ("never" in lower_text or "not received" in lower_text or "missing" in lower_text or "lost" in lower_text):
            issue_type = "Missing Package"
        elif fraud_claim:
            issue_type = "Fraud Claim"
        elif legal_threat:
            issue_type = "Legal Threat"
        elif medical_mention:
            issue_type = "Medical Inquiry"
        elif "return" in lower_text:
            issue_type = "Return Request"
        elif "cancel" in lower_text or "fee" in lower_text:
            issue_type = "Billing Fee Dispute"
        else:
            issue_type = "General Inquiry"

        # 4. Sentiment & Urgency
        if legal_threat or fraud_claim or medical_mention or "unacceptable" in lower_text or "furious" in lower_text:
            urgency = "High"
            sentiment = "Angry"
        elif "frustrated" in lower_text or "disappointed" in lower_text or "again" in lower_text:
            urgency = "Medium"
            sentiment = "Frustrated"
        elif "please" in lower_text or "thanks" in lower_text:
            urgency = "Low"
            sentiment = "Polite"
        else:
            urgency = "Medium"
            sentiment = "Neutral"

        return {
            "sanitized_text": sanitized,
            "issue_type": issue_type,
            "sentiment": sentiment,
            "urgency": urgency,
            "legal_threat": legal_threat,
            "fraud_claim": fraud_claim,
            "medical_mention": medical_mention,
            "entities": entities
        }

intent_agent = IntentAgent()
