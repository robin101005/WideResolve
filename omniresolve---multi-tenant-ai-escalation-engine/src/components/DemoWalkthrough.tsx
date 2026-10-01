import React, { useState } from 'react';
import { executePipeline } from '../lib/mockEngine';
import { CaseFile } from '../lib/types';
import { AgentTraceModal } from './AgentTraceModal';
import { CaseBriefModal } from './CaseBriefModal';
import { Play, CheckCircle2, Clock, AlertTriangle, ArrowRight, Shield, Layers, FileText } from 'lucide-react';

export const DemoWalkthrough: React.FC = () => {
  const [activeDemoCase, setActiveDemoCase] = useState<CaseFile | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<CaseFile | null>(null);
  const [selectedBrief, setSelectedBrief] = useState<CaseFile | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const demoCases = [
    {
      num: 1,
      title: 'QuickCart Double Charge Glitch',
      client: 'quickcart' as const,
      customer: 'QC-CUST-103',
      order: 'QC-ORD-8901',
      complaint: 'I noticed two identical charges of $42.50 on my credit card for order QC-ORD-8901. Please refund the duplicate!',
      expectedOutcome: 'AUTO_RESOLVE',
      expectedDetail: 'Autonomous refund of $42.50 executed to original card. Zero human latency.',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200'
    },
    {
      num: 2,
      title: 'TeleNet 48-Hour Outage SLA Credit',
      client: 'telenet' as const,
      customer: 'TN-CUST-102',
      order: 'TN-ORD-8903',
      complaint: 'Our fiber broadband was completely down during the documented 48-hour outage on TN-ORD-8903. I request a service credit.',
      expectedOutcome: 'RESOLVE_WITH_APPROVAL',
      expectedDetail: 'Prepared $35.00 courtesy credit. TeleNet Outage §2.2 requires supervisor NOC check.',
      badgeColor: 'bg-amber-50 text-amber-700 border-amber-200'
    },
    {
      num: 3,
      title: 'CareLink Billing with Adverse Drug Reaction',
      client: 'carelink' as const,
      customer: 'CL-CUST-104',
      order: 'CL-ORD-8904',
      complaint: 'I was charged twice for copay on CL-ORD-8904, and also I took the medicine prescribed and my throat is swelling and I have severe chest pain.',
      expectedOutcome: 'ESCALATE (Immediate Clinical Safety)',
      expectedDetail: 'Safety §4.2 Hard Rule triggers immediate transfer to human nursing staff. Zero AI clinical advice.',
      badgeColor: 'bg-rose-50 text-rose-700 border-rose-200'
    }
  ];

  const runDemo = async (scenario: typeof demoCases[0]) => {
    setIsRunning(true);
    try {
      const res = await executePipeline(
        scenario.client,
        scenario.customer,
        scenario.complaint,
        scenario.order
      );
      setActiveDemoCase(res);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold uppercase text-indigo-600">Step 13 Golden Demo</span>
          <span className="text-slate-300">·</span>
          <span className="text-xs text-slate-500">Live Production Verification</span>
        </div>
        <h1 className="text-lg font-bold text-slate-900 mt-1">The 3 Golden Demonstration Cases</h1>
        <p className="text-xs text-slate-600 mt-1 max-w-3xl leading-relaxed">
          Demonstrates how the WideResolve shared engine dynamically adjusts between fully autonomous resolution,
          supervised one-click approval, and immediate human clinical escalation across 3 distinct industries.
        </p>
      </div>

      {/* 3 Golden Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {demoCases.map(demo => (
          <div
            key={demo.num}
            className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between hover:border-slate-300 transition-all space-y-4"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-slate-400">Case 0{demo.num}</span>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${demo.badgeColor}`}>
                  {demo.expectedOutcome}
                </span>
              </div>

              <h3 className="text-sm font-bold text-slate-900">{demo.title}</h3>
              <div className="text-[11px] text-slate-500 font-mono">
                Tenant: {demo.client.toUpperCase()} · Order: {demo.order}
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-800">
                "{demo.complaint}"
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {demo.expectedDetail}
              </p>
            </div>

            <button
              onClick={() => runDemo(demo)}
              disabled={isRunning}
              className="w-full py-2 px-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-sm"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Execute Golden Case 0{demo.num}</span>
            </button>
          </div>
        ))}
      </div>

      {/* Active Demo Execution Output */}
      {activeDemoCase && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-slate-900">{activeDemoCase.caseId}</span>
                <span className="text-xs text-slate-300">·</span>
                <span className="text-xs uppercase font-semibold text-slate-600">{activeDemoCase.clientId}</span>
                <span className="text-xs text-slate-300">·</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                  activeDemoCase.status === 'AUTO_RESOLVED' ? 'bg-emerald-50 text-emerald-700' :
                  activeDemoCase.status === 'WAITING_APPROVAL' ? 'bg-amber-50 text-amber-700' :
                  'bg-rose-50 text-rose-700'
                }`}>
                  {activeDemoCase.status.replace(/_/g, ' ')}
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-1">
                Pipeline Execution Result
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedTrace(activeDemoCase)}
                className="px-3 py-1.5 border border-slate-200 hover:bg-slate-100 rounded-lg text-xs font-medium text-slate-800 transition-colors cursor-pointer"
              >
                Inspect 7-Step Trace
              </button>
              {activeDemoCase.caseBrief && (
                <button
                  onClick={() => setSelectedBrief(activeDemoCase)}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium transition-colors cursor-pointer"
                >
                  View Case Brief
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 font-medium block">Diagnosed Issue & Sentiment:</span>
              <span className="font-bold text-slate-900 text-sm mt-0.5 block">{activeDemoCase.intent.issueType}</span>
              <span className="text-slate-600 mt-1 block">Sentiment: {activeDemoCase.intent.sentiment} ({activeDemoCase.intent.urgency} Urgency)</span>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 font-medium block">Multi-Factor Confidence:</span>
              <span className="font-bold font-mono text-slate-900 text-sm mt-0.5 block">
                {(activeDemoCase.escalationDecision.confidence * 100).toFixed(1)}%
              </span>
              <span className="text-slate-600 mt-1 block">
                Threshold: {(activeDemoCase.escalationDecision.confidenceBreakdown.tenantThreshold * 100).toFixed(0)}%
              </span>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 font-medium block">Disbursed / Credit Action:</span>
              <span className="font-bold text-slate-900 text-sm mt-0.5 block font-mono">
                {activeDemoCase.proposedResolution.amount > 0 ? `$${activeDemoCase.proposedResolution.amount.toFixed(2)}` : 'None ($0.00)'}
              </span>
              <span className="text-slate-600 mt-1 block truncate">
                {activeDemoCase.proposedResolution.policyCitation}
              </span>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
            <span className="font-semibold text-slate-800 block">Generated Customer Response:</span>
            <p className="text-slate-700 leading-relaxed font-sans">
              "{activeDemoCase.proposedResolution.customerMessage}"
            </p>
          </div>
        </div>
      )}

      {/* Architecture Topology Diagram */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-600" />
          <span>WideResolve Architecture Diagram</span>
        </h3>

        <div className="p-5 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed">
          <pre>{`
  [Customer Inbound Complaint]
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. Intent Agent (PII Masking, Threat Triage, Regex Guard)   │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 2. Customer History Agent (Tier, LTV, Repeat Disputers)     │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 3. Order / Transaction Agent (Ledger Check, Carrier GPS)    │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 4. Policy / RAG Search (BM25 + Cosine, Tenant Isolated)     │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 5. Root Cause Agent (2-3 Hypotheses, Evidence & Margin)     │
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 6. Resolution Agent (Proposed Action, Policy Citation, Tone)│
  └─────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ 7. Deterministic Escalation Gate (NEVER LLM · Hard Rules)   │
  │    confidence = 0.4*evid + 0.3*pol + 0.2*rc + 0.1*hist      │
  └───────────────┬─────────────────────────────┬───────────────┘
                  │                             │
    Hard Rule or  │                             │ Conf >= Threshold &
    Conf < 0.60   │                             │ Policy Engine Allowed
                  ▼                             ▼
       ┌────────────────────┐         ┌────────────────────┐
       │      ESCALATE      │         │    AUTO_RESOLVE    │
       │ (Generate Brief)   │         │ (Immediate Payout) │
       └──────────┬─────────┘         └─────────┬──────────┘
                  │                             │
                  ▼                             ▼
       ┌────────────────────────────────────────────────────────┐
       │ SHA-256 Hash-Chained Immutable Audit Log Ledger        │
       │ sha256(prev_hash + timestamp + case_id + action + payload)│
       └────────────────────────────────────────────────────────┘
          `}</pre>
        </div>
      </div>

      {/* Modals */}
      <AgentTraceModal
        caseFile={selectedTrace}
        onClose={() => setSelectedTrace(null)}
      />

      <CaseBriefModal
        caseFile={selectedBrief}
        onClose={() => setSelectedBrief(null)}
      />
    </div>
  );
};
