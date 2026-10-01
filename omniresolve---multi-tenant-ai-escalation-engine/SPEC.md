# WideResolve: Widesoftech AI Customer Escalation Resolution Platform

## 1. Executive Summary & Vision
WideResolve is an enterprise B2B platform designed for **Widesoftech** to automate customer support escalation management across distinct client industries while maintaining rigorous deterministic guardrails. 

Customer complaints are often unpredictable, emotionally charged, and high-risk. A pure LLM approach risks hallucinating refunds, violating compliance rules, leaking cross-tenant data, or giving inappropriate medical advice. WideResolve solves this by decoupling **probabilistic reasoning** (intent extraction, root cause hypotheses, customer empathy messages) from **deterministic safety gates** (policy checks, financial limits, multi-tenant isolation, hard escalation triggers, and hash-chained audit trails).

### Supported B2B Tenants
1. **QuickCart** (E-Commerce): Fast fulfillment, high order volume, returns, missing packages, courier double charges.
2. **TeleNet** (Telecommunications): High recurring subscription volume, broadband/5G outage credits, equipment returns, contract billing disputes.
3. **CareLink** (Healthcare Billing & Scheduling): Outpatient clinics, copay billing disputes, insurance reconciliation, appointment reschedules. **Strict clinical firewall**: any clinical, symptom, or medication inquiry is immediately escalated to human staff.

---

## 2. Core Architecture & Tenancy Model

### 2.1 Multi-Tenant Isolation
- **One Shared Engine**: A single resilient pipeline processes complaints across all clients.
- **Tenant Configuration Packs (`configs/{client_id}.yaml`)**: Defines authority limits, confidence thresholds, allowed tools, hard escalation overrides, and brand tone.
- **Data Isolation**: Every database table (`customers`, `orders`, `payments`, `tickets`, `refunds`, `audit_log`) contains a mandatory `client_id` foreign key. All queries and tool executions enforce strict tenant scoping.
- **Cross-Tenant RAG Isolation**: Policy knowledge chunks are tagged with `client_id`. Retrieval mechanisms enforce hard partition filters so QuickCart policies can never leak into CareLink answers.

### 2.2 Pipeline Topology
The workflow orchestrates 7 sequential agentic and deterministic stages:

```
[Customer Complaint]
        │
        ▼
1. Intent Agent (PII Masking, Intent Extraction, Risk Triage)
        │
        ▼
2. Customer History Agent (Tier, LTV, Repeat Contact Rate, Past Tickets)
        │
        ▼
3. Order/Transaction Agent (Ledger, Delivery Status, System Discrepancies)
        │
        ▼
4. Policy / RAG Agent (Tenant-Scoped Clause Retrieval & Citation Matching)
        │
        ▼
5. Root Cause Agent (2-3 Ranked Hypotheses, Evidence & Margin Calculation)
        │
        ▼
6. Resolution Agent (Proposed Action, Compensation Calculation, Message Draft)
        │
        ▼
7. Escalation Gate (Deterministic Hard Rules + Multi-Factor Confidence Scoring)
        │
        ├──▶ AUTO_RESOLVE (Execute Refund/Action + Store in Audit Chain)
        ├──▶ RESOLVE_WITH_APPROVAL (Queue to Human Approver with Pre-filled Action)
        └──▶ ESCALATE (Generate Comprehensive Case Brief for Senior Agent)
```

---

## 3. The 3 Outcomes

1. **`AUTO_RESOLVE`**:
   - The complaint matches verified system facts.
   - The proposed refund or credit is within the client's automated authority limit.
   - Confidence score exceeds the tenant threshold (QuickCart: 0.85, TeleNet: 0.88, CareLink: 0.95).
   - Zero hard escalation rules triggered.
   - Policy engine approves transaction; money action executed immediately; customer receives immediate resolution.

2. **`RESOLVE_WITH_APPROVAL`**:
   - Proposed resolution has high confidence ($\ge 0.60$), but either:
     - Amount exceeds instant auto-resolve authority yet remains within tier manager limits.
     - Ambiguity margin requires human verification (e.g., carrier marked delivered but customer disputes receipt).
   - Case is placed into the `WAITING_APPROVAL` queue with pre-calculated recommendations. A one-click approval or rejection takes place.

3. **`ESCALATE`**:
   - Triggered immediately by hard rules (legal threats, fraud/chargeback claims, medical mentions in healthcare, 3rd repeat complaint, VIP churn risk) or confidence $< 0.60$.
   - Generates a structured **Case Brief** for human agents containing summary, evidence timeline, policy citations, root-cause hypotheses, and escalation rationale.

---

## 4. Proposed Repository Folder Structure

```
├── SPEC.md                      # System architectural specification and design document
├── README.md                    # Setup guide, architecture diagram, demo walkthrough
├── package.json                 # Node dependencies for Fullstack Client Web & Ops app
├── tsconfig.json                # TypeScript compiler configuration
├── vite.config.ts               # Vite configuration with Tailwind CSS v4
├── metadata.json                # AI Studio application metadata
│
├── configs/                     # Tenant YAML configuration packs
│   ├── quickcart.yaml           # QuickCart e-commerce rules, limits & tools
│   ├── telenet.yaml             # TeleNet telecom SLA, credit caps & outage policies
│   └── carelink.yaml            # CareLink healthcare strict billing/clinical boundaries
│
├── policies/                    # Tenant policy documents with numbered clauses
│   ├── quickcart_policies.md    # QuickCart refund §1.1-§3.4, shipping §4.1-§5.2
│   ├── telenet_policies.md      # TeleNet billing §1.1-§2.3, outage SLA §3.1-§4.2
│   └── carelink_policies.md     # CareLink billing §1.1-§3.2, safety clinical firewall §4.1
│
├── db/                          # Database definitions & mock seeding
│   ├── schema.sql               # SQLite multi-tenant DDL (client_id on all tables)
│   ├── mock_db.py               # Python SQLite generator with 9 planted scenarios
│   └── seed_data.json           # Portable mock data representation
│
├── engine/                      # Core backend pipeline & deterministic engines
│   ├── __init__.py
│   ├── types.py                 # CaseFile, Resolution, AuditRecord Pydantic types
│   ├── tools.py                 # Tenant-scoped data access tools
│   ├── policy_engine.py         # Deterministic financial & policy validation rules
│   ├── rag.py                   # Tenant-isolated hybrid vector/keyword policy retriever
│   ├── escalation_gate.py       # Hard rule checker + multi-factor confidence engine
│   ├── audit_chain.py           # Cryptographic SHA-256 hash-chained audit log
│   └── graph.py                 # Workflow pipeline execution engine
│
├── agents/                      # Specialized agent modules
│   ├── __init__.py
│   ├── pii_sanitizer.py         # Regex PII scrubber (phone, email, cards)
│   ├── intent_agent.py          # Structured complaint classification
│   ├── history_agent.py         # Customer lifetime value & ticket history analyzer
│   ├── order_agent.py           # Transaction ledger & tracking gap detector
│   ├── policy_agent.py          # Policy citation matcher
│   ├── root_cause_agent.py      # Hypothesis ranking & margin calculator
│   └── resolution_agent.py      # Resolution action generator & response drafter
│
├── api/                         # FastAPI / Express application routes
│   ├── main.py                  # Python FastAPI backend server
│   └── server.ts                # Fullstack Node/Express server serving APIs & React
│
├── tests/                       # Automated test suites
│   ├── test_policy_engine.py    # Test 6 financial & permission block rules
│   ├── test_rag_isolation.py    # Test tenant RAG isolation & similarity scoring
│   ├── test_escalation_gate.py  # Test all deterministic hard escalation rules
│   ├── test_audit_tamper.py     # Test cryptographic hash-chain tamper detection
│   └── test_agents.py           # Unit tests for intent, order, and history agents
│
├── evaluation/                  # Comprehensive evaluation & safety test suite
│   ├── evaluate.py              # 60 labelled test cases, confusion matrix & metrics
│   ├── prompt_injection_tests.py# Adversarial injection tests
│   └── safety_tests.py          # CareLink medical safety and cross-tenant leak tests
│
└── src/                         # Dual Web Frontends (Client Portal + Mobile Ops Console)
    ├── App.tsx                  # Master application orchestrator
    ├── components/
    │   ├── ClientPortal.tsx     # B2B Client view (case list, live trace, chat widget)
    │   ├── MobileOpsConsole.tsx # Company internal mobile escalation queue & approvals
    │   ├── EvaluationBench.tsx  # Live test bench (confusion matrix, injection, safety)
    │   ├── AuditChainViewer.tsx # Interactive hash-chain verifier with tamper tester
    │   ├── PolicyExplorer.tsx   # Policy clauses and YAML config pack inspector
    │   └── ChatWidget.tsx       # Embeddable customer complaint widget
    └── lib/
        ├── types.ts             # Shared frontend/backend TypeScript contracts
        └── mockEngine.ts        # In-memory execution bridge & data stores
```

---

## 5. Planted Scenarios
1. **Double Charge** (QuickCart): Customer billed twice for order `QC-8901`; transaction ledger confirms duplicate $42.50 charges. *Expected: AUTO_RESOLVE*.
2. **Late Delivery** (QuickCart): Package delayed past SLA; tracked delay is 5 days. *Expected: AUTO_RESOLVE ($10 courtesy credit)*.
3. **Outage Billing** (TeleNet): Customer experienced 48h broadband blackout during severe network outage. *Expected: RESOLVE_WITH_APPROVAL (Service credit of $35.00)*.
4. **Duplicate Medical Bill** (CareLink): Patient billed twice for lab work copay of $50.00. *Expected: AUTO_RESOLVE (Refund duplicate copay)*.
5. **Fraud / Unauthorized Charge Claim** (QuickCart): Customer claims credit card stolen. *Expected: ESCALATE (Hard rule: Fraud claim)*.
6. **Repeat Complainer** (TeleNet): Customer with 3 open/recent tickets within 30 days. *Expected: ESCALATE (Hard rule: 3rd repeat contact)*.
7. **Legal / Regulatory Threat** (CareLink): Customer threatens HIPAA lawsuit or lawyer. *Expected: ESCALATE (Hard rule: Legal threat)*.
8. **VIP Customer with Churn Risk** (TeleNet): Tier 1 enterprise VIP threatening cancellation. *Expected: ESCALATE (Hard rule: VIP churn risk)*.
9. **Delivered vs Not Received** (QuickCart): Courier status claims "Delivered to porch", but customer insists never received. *Expected: RESOLVE_WITH_APPROVAL or ESCALATE (Contradictory evidence)*.
