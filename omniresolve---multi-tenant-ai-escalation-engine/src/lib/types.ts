export type ClientId = 'quickcart' | 'telenet' | 'carelink';

export type CaseStatus =
  | 'PENDING'
  | 'AUTO_RESOLVED'
  | 'WAITING_APPROVAL'
  | 'ESCALATED'
  | 'APPROVED_AND_RESOLVED'
  | 'REJECTED'
  | 'REOPENED_ESCALATED';

export interface CustomerProfile {
  id: string;
  clientId: ClientId;
  name: string;
  email: string;
  phone: string;
  tier: 'Standard' | 'Gold' | 'VIP';
  ltv: number;
  churnRisk: boolean;
  repeatComplaintCount: number;
  pastTicketCount: number;
  historyConsistency: number;
}

export interface OrderRecord {
  id: string;
  clientId: ClientId;
  customerId: string;
  orderDate: string;
  status: string;
  totalAmount: number;
  carrierStatus: string;
  deliveryNotes: string;
  paymentCount?: number;
  capturedTotal?: number;
  duplicateChargesFound?: boolean;
  duplicateAmount?: number;
  deliveryGap?: boolean;
  outageRecorded?: boolean;
  contradictions?: string[];
  evidenceAgreement?: number;
}

export interface PolicyMatch {
  clauseId: string;
  title: string;
  citation: string;
  text: string;
  similarityScore: number;
}

export interface RootCauseHypothesis {
  rank: number;
  hypothesis: string;
  evidence: string;
  confidence: number;
}

export interface ProposedResolution {
  proposedAction: string;
  amount: number;
  policyCitation: string;
  customerMessage: string;
}

export interface EscalationDecision {
  outcome: 'AUTO_RESOLVE' | 'RESOLVE_WITH_APPROVAL' | 'ESCALATE';
  status: CaseStatus;
  confidence: number;
  reasons: string[];
  hardRulesTriggered: string[];
  escalateTo?: 'Compliance Lead & Account Manager' | 'Billing Operations Lead' | 'Senior Tier-2 Support Engineer' | 'General Support Lead';
  confidenceBreakdown: {
    evidenceAgreement: number;
    policyMatch: number;
    rootCauseMargin: number;
    historyConsistency: number;
    totalConfidence: number;
    tenantThreshold: number;
  };
}

export interface CaseBrief {
  caseId: string;
  clientId: ClientId;
  timestamp: string;
  summary: string;
  escalateTo?: string;
  evidenceTimeline: string[];
  policyCitations: string[];
  recommendedAction: {
    action: string;
    amount: number;
    suggestedMessage: string;
  };
  whyEscalated: string[];
  confidenceScore: number;
  hardRulesTriggered: string[];
  reopenReason?: string;
}

export interface CaseFile {
  caseId: string;
  clientId: ClientId;
  customerId: string;
  orderId?: string;
  rawComplaint: string;
  sanitizedComplaint: string;
  intent: {
    issueType: string;
    sentiment: string;
    urgency: string;
    legalThreat: boolean;
    fraudClaim: boolean;
    medicalMention: boolean;
    entities: {
      orderId?: string;
      amount?: number;
    };
  };
  customerProfile?: CustomerProfile;
  orderDetails?: OrderRecord;
  relevantPolicies: PolicyMatch[];
  rootCauseHypotheses: RootCauseHypothesis[];
  rootCauseMargin: number;
  proposedResolution: ProposedResolution;
  escalationDecision: EscalationDecision;
  status: CaseStatus;
  caseBrief?: CaseBrief;
  createdAt: string;
  aiMetadata?: {
    model: string;
    latencyMs: number;
    live: boolean;
    rawOutput?: string;
  };
}

export interface AuditRecord {
  id: number;
  clientId: ClientId;
  caseId: string;
  timestamp: string;
  action: string;
  payload: string;
  previousHash: string;
  currentHash: string;
}

export interface TenantConfig {
  clientId: ClientId;
  clientName: string;
  industry: string;
  authorityLimit: number;
  confidenceThreshold: number;
  hardEscalationRules: string[];
  allowedTools: string[];
  tone: string;
  clinicalFirewall?: boolean;
}
