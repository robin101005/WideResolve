import React, { useState } from 'react';
import { CaseFile } from '../lib/types';
import { X, CheckCircle2, XCircle, AlertTriangle, FileText, ArrowRight } from 'lucide-react';
import { approveCase, rejectCase } from '../lib/mockEngine';

interface CaseBriefModalProps {
  caseFile: CaseFile | null;
  onClose: () => void;
  onActionComplete?: () => void;
}

export const CaseBriefModal: React.FC<CaseBriefModalProps> = ({ caseFile, onClose, onActionComplete }) => {
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!caseFile) return null;
  const brief = caseFile.caseBrief;

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await approveCase(caseFile.caseId, 'OPERATIONS_DIRECTOR_MGR');
      if (onActionComplete) onActionComplete();
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    setIsSubmitting(true);
    try {
      await rejectCase(caseFile.caseId, 'OPERATIONS_DIRECTOR_MGR', rejectReason);
      if (onActionComplete) onActionComplete();
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-900">{caseFile.caseId}</span>
              <span className="text-xs text-slate-300">·</span>
              <span className="text-xs font-medium uppercase text-slate-500">{caseFile.clientId}</span>
              <span className="text-xs text-slate-300">·</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                caseFile.status === 'AUTO_RESOLVED' ? 'bg-emerald-50 text-emerald-700' :
                caseFile.status === 'WAITING_APPROVAL' ? 'bg-amber-50 text-amber-700' :
                'bg-rose-50 text-rose-700'
              }`}>
                {caseFile.status.replace(/_/g, ' ')}
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-900 mt-1 flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-700" />
              <span>Widesoftech Support · Escalation Case Brief</span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1 text-xs">
          {/* Assigned Human Role from Escalation Matrix */}
          <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-lg flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-indigo-700 uppercase tracking-wider block">
                Designated Human Role (Escalation Matrix)
              </span>
              <span className="text-sm font-bold text-slate-900">
                {brief?.escalateTo || caseFile.escalationDecision.escalateTo || 'Compliance Lead & Account Manager'}
              </span>
            </div>
            <span className="px-2.5 py-1 bg-indigo-100 text-indigo-900 rounded font-medium text-[11px]">
              Ready for Human Review
            </span>
          </div>

          {/* Executive Summary */}
          <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-semibold text-slate-900">Executive Summary</h3>
              <span className="inline-flex items-center gap-1 text-[10px] font-mono text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Synthesized by Google Gemini 3.8 Flash
              </span>
            </div>
            <p className="text-slate-700 leading-relaxed">
              {brief?.summary || `Complaint filed regarding ${caseFile.intent.issueType}.`}
            </p>
          </div>

          {/* Why Escalated / Hard Rules */}
          <div className="p-4 bg-rose-50/60 rounded-lg border border-rose-200/80">
            <h3 className="font-semibold text-rose-900 mb-1 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Why Escalated / Gate Decision Rationale</span>
            </h3>
            <ul className="list-disc pl-4 space-y-1 text-rose-800 mt-2">
              {(brief?.whyEscalated || caseFile.escalationDecision.reasons).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>

          {/* Evidence Timeline */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-2">Evidence & Audit Timeline</h3>
            <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 bg-white">
              {(brief?.evidenceTimeline || [
                `1. Raw Complaint: "${caseFile.rawComplaint}"`,
                `2. Order: ${caseFile.orderId || 'None'}`,
                `3. Status: ${caseFile.status}`
              ]).map((event, idx) => (
                <div key={idx} className="p-3 text-slate-700 font-mono text-xs">
                  {event}
                </div>
              ))}
            </div>
          </div>

          {/* Policy Citations */}
          <div>
            <h3 className="font-semibold text-slate-900 mb-2">Governing Policy Citations</h3>
            <div className="space-y-2">
              {brief?.policyCitations && brief.policyCitations.length > 0 ? (
                brief.policyCitations.map((pc, idx) => (
                  <div key={idx} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800">
                    {pc}
                  </div>
                ))
              ) : (
                <p className="text-slate-500 italic">No specific policy citations recorded.</p>
              )}
            </div>
          </div>

          {/* Recommended Action */}
          <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-lg">
            <h3 className="font-semibold text-indigo-900 mb-2">Recommended Autonomous Resolution Action</h3>
            <div className="grid grid-cols-2 gap-4 text-slate-800 mb-3">
              <div>
                <span className="text-slate-500 block">Proposed Action:</span>
                <span className="font-bold text-slate-900">{caseFile.proposedResolution.proposedAction}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Payout / Credit Amount:</span>
                <span className="font-bold text-slate-900 font-mono text-sm">
                  ${caseFile.proposedResolution.amount.toFixed(2)}
                </span>
              </div>
            </div>
            <div className="p-2.5 bg-white border border-indigo-100 rounded text-slate-700">
              <span className="font-medium text-slate-500 block text-[11px] mb-1">Customer Communication Template:</span>
              "{caseFile.proposedResolution.customerMessage}"
            </div>
          </div>

          {/* Reject Reason Input (if toggled) */}
          {showRejectInput && (
            <div className="p-4 border border-rose-300 rounded-lg bg-rose-50 space-y-2">
              <label className="block font-medium text-rose-900">Rejection Rationale (Logged to Audit Chain):</label>
              <textarea
                rows={2}
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                placeholder="State why this proposed resolution was rejected..."
                className="w-full text-xs p-2.5 border border-rose-300 rounded bg-white text-slate-900 focus:outline-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowRejectInput(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={!rejectReason.trim() || isSubmitting}
                  onClick={handleReject}
                  className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-medium disabled:opacity-50"
                >
                  Confirm Rejection
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-mono">
            Confidence: {(caseFile.escalationDecision.confidence * 100).toFixed(1)}%
          </span>
          <div className="flex items-center gap-3">
            {caseFile.status === 'WAITING_APPROVAL' && !showRejectInput && (
              <>
                <button
                  onClick={() => setShowRejectInput(true)}
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  <span>Reject / Override</span>
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Approve & Disburse (${caseFile.proposedResolution.amount.toFixed(2)})</span>
                </button>
              </>
            )}
            {caseFile.status === 'ESCALATED' && (
              <button
                onClick={handleApprove}
                disabled={isSubmitting}
                className="px-4 py-2 border border-indigo-300 text-indigo-700 hover:bg-indigo-50 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
                title="Override AI Escalation and force approval"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Engineer Override (Approve Resolution)</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-medium hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Close Brief
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
