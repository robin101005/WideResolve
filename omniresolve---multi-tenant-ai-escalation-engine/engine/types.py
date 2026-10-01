"""
Core typed data structures for OmniResolve multi-tenant engine.
Compatible with standard library and easily serializable to JSON.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum

class EscalationOutcome(str, Enum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    RESOLVE_WITH_APPROVAL = "RESOLVE_WITH_APPROVAL"
    ESCALATE = "ESCALATE"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"

class BlockReason(str, Enum):
    WRONG_CLIENT_ID = "WRONG_CLIENT_ID"
    CUSTOMER_NOT_ORDER_OWNER = "CUSTOMER_NOT_ORDER_OWNER"
    REFUND_EXCEEDS_PAID = "REFUND_EXCEEDS_PAID"
    DUPLICATE_REFUND = "DUPLICATE_REFUND"
    AMOUNT_ABOVE_AUTHORITY_LIMIT = "AMOUNT_ABOVE_AUTHORITY_LIMIT"
    SELF_APPROVAL_PROHIBITED = "SELF_APPROVAL_PROHIBITED"
    UNKNOWN_ORDER = "UNKNOWN_ORDER"
    INVALID_AMOUNT = "INVALID_AMOUNT"

@dataclass
class Customer:
    id: str
    client_id: str
    name: str
    email: str
    phone: str
    tier: str = "Standard"
    ltv: float = 0.0
    churn_risk: bool = False
    repeat_complaint_count: int = 0
    created_at: str = ""

@dataclass
class Order:
    id: str
    client_id: str
    customer_id: str
    order_date: str
    status: str
    total_amount: float
    carrier_status: Optional[str] = None
    delivery_notes: Optional[str] = None

@dataclass
class Payment:
    id: str
    client_id: str
    order_id: str
    customer_id: str
    amount: float
    status: str
    payment_method: str
    transaction_ref: str
    created_at: str

@dataclass
class Ticket:
    id: str
    client_id: str
    customer_id: str
    order_id: Optional[str]
    issue_type: str
    status: str
    sentiment: str
    complaint_text: str
    created_at: str

@dataclass
class RefundRequest:
    client_id: str
    customer_id: str
    order_id: str
    amount: float
    reason: str
    requester_id: str
    approver_id: Optional[str] = None

    def validate(self):
        if not self.client_id:
            raise ValueError("client_id is required")
        if not self.customer_id:
            raise ValueError("customer_id is required")
        if not self.order_id:
            raise ValueError("order_id is required")
        if self.amount <= 0:
            raise ValueError("amount must be greater than 0")
        if not self.reason:
            raise ValueError("reason is required")
        if not self.requester_id:
            raise ValueError("requester_id is required")

@dataclass
class PolicyValidationResult:
    allowed: bool
    status: str  # "ALLOWED", "BLOCKED", "NEEDS_APPROVAL"
    block_reason: Optional[BlockReason] = None
    message: str = ""
    client_id: str = ""
    order_id: str = ""
    requested_amount: float = 0.0
    authority_limit: float = 0.0

@dataclass
class CaseFile:
    case_id: str
    client_id: str
    customer_id: str
    order_id: Optional[str] = None
    raw_complaint: str = ""
    sanitized_complaint: str = ""
    intent: Dict[str, Any] = field(default_factory=dict)
    customer_profile: Optional[Dict[str, Any]] = None
    order_details: Optional[Dict[str, Any]] = None
    relevant_policies: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_margin: float = 0.0
    proposed_resolution: Dict[str, Any] = field(default_factory=dict)
    escalation_decision: Dict[str, Any] = field(default_factory=dict)
    status: str = "PENDING"  # PENDING, AUTO_RESOLVED, WAITING_APPROVAL, ESCALATED, REJECTED
    case_brief: Optional[Dict[str, Any]] = None
    created_at: str = ""
