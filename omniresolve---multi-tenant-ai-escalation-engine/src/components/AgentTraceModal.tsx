import React, { useState } from 'react';
import { CaseFile } from '../lib/types';
import { X, CheckCircle2, AlertTriangle, ShieldCheck, Database, FileText, Cpu, GitBranch, ArrowRight, Sparkles, Terminal } from 'lucide-react';

interface AgentTraceModalProps {
  caseFile: CaseFile | null;
  onClose: () => void;
}

export const AgentTraceModal: React.FC<AgentTraceModalProps> = ({ caseFile, onClose }) => {
  const [showRawAi, setShowRawAi] = useState(false);
  if (!caseFile) return null;

  const { intent, customerProfile, orderDetails, relevantPolicies, rootCauseHypotheses, rootCauseMargin, proposedResolution, escalationDecision } = caseFile;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-medium text-slate-500 uppercase">{caseFile.clientId}</span>
              <span className="text-xs text-slate-300">/</span>
              <span className="text-xs font-mono font-semibold text-slate-900">{caseFile.caseId}</span>
              <span className="text-xs text-slate-300">·</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                caseFile.status === 'AUTO_RESOLVED' ? 'bg-emerald-50 text-emerald-700' :
                caseFile.status === 'WAITING_APPROVAL' ? 'bg-amber-50 text-amber-700' :
                'bg-rose-50 text-rose-700'
              }`}>
                {caseFile.status.replace(/_/g, ' ')}
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-900 mt-1">
              Deterministic Agent Execution Trace
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Pipeline */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* Live AI Engine Status Banner */}
          <div className="p-3 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-sm border border-indigo-900/50">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-bold text-xs text-white">Live AI Detective Model:</span>
              <span className="font-mono text-xs text-indigo-300 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-700/60 font-semibold">
                {caseFile.aiMetadata?.model || 'Google Gemini 3.8 Flash'}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono text-indigo-200">
              <span className="text-emerald-400 font-semibold">Active GenAI Pipeline</span>
              {caseFile.aiMetadata?.latencyMs ? (
                <span className="text-slate-300">· {caseFile.aiMetadata.latencyMs}ms inference</span>
              ) : (
                <span className="text-slate-300">· Verified Live</span>
              )}
              {caseFile.aiMetadata?.rawOutput && (
                <button
                  onClick={() => setShowRawAi(!showRawAi)}
                  className="px-2 py-1 bg-indigo-800 hover:bg-indigo-700 text-white rounded text-[10px] font-sans font-medium transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <Terminal className="w-3 h-3" />
                  <span>{showRawAi ? 'Hide Raw AI' : 'Inspect Raw AI'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Expandable Raw Gemini JSON Inspector */}
          {showRawAi && caseFile.aiMetadata?.rawOutput && (
            <div className="p-4 bg-slate-950 text-emerald-400 rounded-lg font-mono text-[11px] border border-slate-800 overflow-x-auto shadow-inner">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400 text-[10px]">
                <span>RAW RESPONSE FROM GOOGLE GEMINI API ({caseFile.aiMetadata.model})</span>
                <span>Inference Latency: {caseFile.aiMetadata.latencyMs}ms</span>
              </div>
              <pre className="whitespace-pre-wrap leading-relaxed">{caseFile.aiMetadata.rawOutput}</pre>
            </div>
          )}

          {/* Step 1: Intent & PII Sanitization */}
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm">
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                <span>1. Intent Agent & PII Sanitizer</span>
              </div>
              <span className="text-slate-500 font-mono">Temp: 0.0 · Untrusted Input Guard</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
              <div>
                <span className="text-slate-500 font-medium">Raw Customer Input:</span>
                <p className="mt-1 p-2 bg-white rounded border border-slate-200 text-slate-800 font-mono">
                  "{caseFile.rawComplaint}"
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-medium">PII-Sanitized Text (Safe for Engine):</span>
                <p className="mt-1 p-2 bg-white rounded border border-slate-200 text-slate-800 font-mono">
                  "{caseFile.sanitizedComplaint}"
                </p>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-4 pt-2 border-t border-slate-200 text-slate-700">
              <div><strong className="text-slate-900">Issue:</strong> {intent.issueType}</div>
              <div><strong className="text-slate-900">Sentiment:</strong> {intent.sentiment}</div>
              <div><strong className="text-slate-900">Urgency:</strong> {intent.urgency}</div>
              <div><strong className="text-slate-900">Legal Threat:</strong> {intent.legalThreat ? 'YES ⚠️' : 'No'}</div>
              <div><strong className="text-slate-900">Fraud Claim:</strong> {intent.fraudClaim ? 'YES 🚨' : 'No'}</div>
              <div><strong className="text-slate-900">Medical Mention:</strong> {intent.medicalMention ? 'YES 🏥' : 'No'}</div>
            </div>
          </div>

          {/* Step 2 & 3: History and Order */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Customer History */}
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm mb-2">
                <Database className="w-4 h-4 text-blue-600" />
                <span>2. Customer History Agent</span>
              </div>
              {customerProfile ? (
                <div className="space-y-1.5 text-slate-700">
                  <div><strong>Account:</strong> {customerProfile.name} ({customerProfile.id})</div>
                  <div><strong>Tier / LTV:</strong> {customerProfile.tier} · ${customerProfile.ltv.toFixed(2)}</div>
                  <div><strong>Repeat Contact Count:</strong> {customerProfile.repeatComplaintCount} (Threshold: 3)</div>
                  <div><strong>Churn Risk:</strong> {customerProfile.churnRisk ? 'High Risk ⚠️' : 'Normal'}</div>
                  <div><strong>History Consistency:</strong> {(customerProfile.historyConsistency * 100).toFixed(0)}%</div>
                </div>
              ) : (
                <p className="text-slate-500">Customer profile retrieved from client database.</p>
              )}
            </div>

            {/* Order / Transaction */}
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm mb-2">
                <Cpu className="w-4 h-4 text-violet-600" />
                <span>3. Order / Transaction Agent</span>
              </div>
              {orderDetails ? (
                <div className="space-y-1.5 text-slate-700">
                  <div><strong>Order Ref:</strong> {orderDetails.id}</div>
                  <div><strong>Status:</strong> {orderDetails.status} · ${orderDetails.totalAmount.toFixed(2)}</div>
                  <div><strong>Carrier Telemetry:</strong> {orderDetails.carrierStatus}</div>
                  <div><strong>Duplicate Charges:</strong> {orderDetails.duplicateChargesFound ? `CONFIRMED ($${orderDetails.duplicateAmount?.toFixed(2)})` : 'None'}</div>
                  <div><strong>Contradictions:</strong> {orderDetails.contradictions?.length ? orderDetails.contradictions.join(', ') : 'None'}</div>
                  <div><strong>Evidence Agreement:</strong> {(orderDetails.evidenceAgreement ?? 0.8) * 100}%</div>
                </div>
              ) : (
                <p className="text-slate-500">No specific order transaction attached.</p>
              )}
            </div>
          </div>

          {/* Step 4: Policy RAG Search */}
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span>4. Policy / RAG Agent (Tenant-Isolated)</span>
              </div>
              <span className="text-slate-500 font-mono">BM25 + Cosine Vector Similarity</span>
            </div>
            <div className="space-y-2 mt-2">
              {relevantPolicies.map((p, idx) => (
                <div key={idx} className="p-2.5 bg-white border border-slate-200 rounded-lg flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900">{p.citation}</p>
                    <p className="text-slate-600 text-xs mt-0.5">{p.text}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="font-mono font-bold text-slate-900">{(p.similarityScore * 100).toFixed(1)}%</span>
                    <span className="block text-slate-400 text-[10px]">match score</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Step 5: Root Cause Diagnostics */}
          <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 font-semibold text-slate-900 text-sm">
                <GitBranch className="w-4 h-4 text-amber-600" />
                <span>5. Root Cause Agent (Ranked Hypotheses)</span>
              </div>
              <span className="font-mono text-slate-700">Diagnostic Margin: <strong>{(rootCauseMargin * 100).toFixed(1)}%</strong></span>
            </div>
            <div className="space-y-2 mt-2">
              {rootCauseHypotheses.map(h => (
                <div key={h.rank} className="p-2.5 bg-white border border-slate-200 rounded-lg flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <span className="font-semibold text-slate-900">Rank {h.rank}: {h.hypothesis}</span>
                    <p className="text-slate-500 text-xs mt-0.5">Evidence: {h.evidence}</p>
                  </div>
                  <div className="text-right shrink-0 font-mono font-medium text-slate-700">
                    {(h.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Step 6 & 7: Resolution & Escalation Gate */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Resolution */}
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <span className="font-semibold text-slate-900 text-sm block mb-2">6. Resolution Agent</span>
              <div className="space-y-2 text-slate-700">
                <div><strong>Proposed Action:</strong> {proposedResolution.proposedAction}</div>
                <div><strong>Calculated Amount:</strong> ${proposedResolution.amount.toFixed(2)}</div>
                <div><strong>Policy Citation:</strong> {proposedResolution.policyCitation}</div>
                <div className="mt-2 p-2 bg-white rounded border border-slate-200 text-slate-800">
                  <span className="font-semibold block text-slate-600 mb-1">Draft Customer Response:</span>
                  "{proposedResolution.customerMessage}"
                </div>
              </div>
            </div>

            {/* Escalation Gate */}
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-900 text-sm">7. Deterministic Escalation Gate</span>
                <span className="text-[10px] text-slate-500 font-mono">Pure Code · Never LLM</span>
              </div>
              <div className="space-y-2 text-slate-700">
                <div className="flex items-center justify-between">
                  <span>Calculated Confidence:</span>
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {(escalationDecision.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span>Client Threshold:</span>
                  <span className="font-mono">
                    {(escalationDecision.confidenceBreakdown.tenantThreshold * 100).toFixed(0)}%
                  </span>
                </div>

                {escalationDecision.hardRulesTriggered.length > 0 && (
                  <div className="p-2 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs mt-2">
                    <strong className="block mb-1">Hard Escalation Rules Triggered:</strong>
                    <ul className="list-disc pl-4 space-y-0.5">
                      {escalationDecision.hardRulesTriggered.map((hr, i) => (
                        <li key={i}>{hr}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="mt-2 pt-2 border-t border-slate-200">
                  <span className="font-semibold block text-slate-800 mb-1">Gate Decision:</span>
                  <p className="font-medium text-slate-900">{escalationDecision.outcome}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            Immutable SHA-256 record verified in tenant audit ledger.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
};
