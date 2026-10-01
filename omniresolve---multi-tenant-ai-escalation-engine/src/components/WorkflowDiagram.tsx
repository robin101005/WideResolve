import React from 'react';
import { Shield, GitBranch, Cpu, Database, FileText, CheckCircle2, AlertTriangle, ArrowRight, UserCheck, Lock } from 'lucide-react';

export const WorkflowDiagram: React.FC = () => {
  const agents = [
    {
      num: 1,
      name: 'Intent Agent',
      job: 'Reads the ticket',
      example: 'Billing dispute, client is annoyed',
      icon: <FileText className="w-4 h-4 text-blue-600" />
    },
    {
      num: 2,
      name: 'Customer History Agent',
      job: 'Looks up client profile and past tickets',
      example: 'Gold tier, third outage ticket in 60 days',
      icon: <Database className="w-4 h-4 text-violet-600" />
    },
    {
      num: 3,
      name: 'Order / Incident Agent',
      job: 'Checks invoices and incident logs',
      example: 'Duplicate charge found; 95 minutes of downtime',
      icon: <Cpu className="w-4 h-4 text-amber-600" />
    },
    {
      num: 4,
      name: 'Policy / RAG Agent',
      job: "Finds the client's contract and SLA clauses",
      example: 'Clause 7.1: duplicate charges credited in full',
      icon: <Shield className="w-4 h-4 text-emerald-600" />
    },
    {
      num: 5,
      name: 'Root Cause Agent',
      job: 'Combines evidence into a cause',
      example: 'Billing retry error, confidence 95%',
      icon: <GitBranch className="w-4 h-4 text-indigo-600" />
    },
    {
      num: 6,
      name: 'Resolution Agent',
      job: 'Proposes the fix with a cited clause',
      example: 'Credit note plus apology',
      icon: <CheckCircle2 className="w-4 h-4 text-teal-600" />
    },
    {
      num: 7,
      name: 'Escalation Gate',
      job: 'Decides auto-resolve or human, and which human',
      example: 'Auto-resolve, or escalate to compliance lead',
      icon: <UserCheck className="w-4 h-4 text-rose-600" />
    }
  ];

  const ruleChecks = [
    { check: 'Amount', condition: "Credit or refund is above the agent's limit", example: 'QuickCart >$50, TeleNet >$40, CareLink >$60' },
    { check: 'Confidence', condition: 'Root cause confidence is below the threshold', example: 'Confidence <0.85 (routes to human review)' },
    { check: 'Evidence', condition: 'Logs and client claim conflict', example: 'Carrier marked Delivered but camera shows no package' },
    { check: 'Contract', condition: 'Clause is ambiguous, missing or contradictory', example: 'Unprecedented clause or RAG similarity <0.20' },
    { check: 'Compliance', condition: 'Healthcare or data-privacy issue, or security incident', example: 'Patient symptoms or unauthorized access (CareLink)' },
    { check: 'Risk words', condition: 'Legal threat', example: 'Attorney, lawsuit, FCC/FTC/HIPAA litigation' },
    { check: 'Pattern', condition: 'Repeat issue or strategic client', example: '≥3 tickets in 60 days or VIP churn risk ($2,400 LTV)' }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto text-xs">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold uppercase text-indigo-600">Hackathon Problem Statement 07</span>
          <span className="text-slate-300">·</span>
          <span className="text-xs text-slate-500">Widesoftech Architecture</span>
        </div>
        <h1 className="text-lg font-bold text-slate-900 mt-1">
          WideResolve: Detective Team Workflow & Block Diagram
        </h1>
        <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
          The AI acts like a detective with a team of helper agents. Each agent does one small job and passes its notes to the next.
          The system then makes one key decision: can the AI resolve this alone, or must a human step in?
        </p>
      </div>

      {/* The 7 Helper Agents Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Section 6: The 7 Helper Agents</h2>
            <p className="text-slate-500 mt-0.5">Sequential notes passed down the investigation chain</p>
          </div>
          <span className="font-mono text-slate-400">Strict Client Isolation</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {agents.map(a => (
            <div key={a.num} className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-3">
              <div className="p-2 bg-white rounded-md border border-slate-200 shrink-0">
                {a.icon}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">
                    Agent {a.num}: {a.name}
                  </span>
                  <span className="font-mono text-slate-400 text-[10px]">#{a.num}</span>
                </div>
                <p className="text-slate-600 text-[11px]">
                  <strong>Job:</strong> {a.job}
                </p>
                <p className="text-indigo-900 font-mono text-[11px] bg-indigo-50/70 p-1.5 rounded border border-indigo-100">
                  Example: "{a.example}"
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 7: When Does the AI Escalate? (Rule Checks Table) */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Section 7: When Does the AI Escalate?</h2>
            <p className="text-slate-500 mt-0.5">Decisions are rule-based checks in code; the LLM only explains them</p>
          </div>
          <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-medium text-[11px]">
            Deterministic Guardrails
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[10px] uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">Check</th>
                <th className="py-2.5 px-3">Escalate When</th>
                <th className="py-2.5 px-3">Widesoftech Implementation Guard</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {ruleChecks.map((rc, idx) => (
                <tr key={idx} className="hover:bg-slate-50/70">
                  <td className="py-2.5 px-3 font-bold text-slate-900">{rc.check}</td>
                  <td className="py-2.5 px-3">{rc.condition}</td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-indigo-700">{rc.example}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Block Diagram Topology */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-slate-900">Section 4 & 5: Block Diagram & Workflow</h2>
        <div className="p-4 bg-slate-900 text-slate-100 rounded-lg font-mono text-[11px] leading-relaxed overflow-x-auto">
          <pre>{`
  [CLIENT PORTAL]
  (Client Company: E-Commerce, Telecom, Healthcare)
  Client logs in ──▶ Enters Ticket Problem ──▶ Submits Inbound Claim
                                                      │
                                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ WIDESOFTECH AGENT PIPELINE                                                  │
  │                                                                             │
  │  [1. Intent] ──▶ [2. History] ──▶ [3. Invoices/Logs] ──▶ [4. SLA Contract]  │
  │                                                                    │        │
  │                                                                    ▼        │
  │  [7. Escalation Decision] ◀── [6. Resolution] ◀── [5. Root Cause Analysis] │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
         [AUTO-RESOLVE]                                    [ESCALATE]
   • Cites SLA Clause (e.g. 7.1)                     • Generates Case Brief
   • Issues invoice credit note                      • Routes to Designated Role:
   • Replies to client in portal                       - Compliance Lead & Account Mgr
                                                       - Billing Operations Lead
                                                       - Senior Tier-2 Support Eng.
                                                                 │
                                                                 ▼
                                                         [ADMIN PORTAL]
                                                   Widesoftech Engineers review,
                                                   Approve or Override decision
          `}</pre>
        </div>
      </div>
    </div>
  );
};
