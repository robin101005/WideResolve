import React, { useState } from 'react';
import { ClientId, CaseFile } from '../lib/types';
import { TENANT_CONFIGS, executePipeline, submitFeedback } from '../lib/mockEngine';
import { Send, CheckCircle2, AlertTriangle, Clock, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-react';

interface ChatWidgetProps {
  clientId: ClientId;
  onCaseCreated?: (newCase: CaseFile) => void;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ clientId, onCaseCreated }) => {
  const [complaintText, setComplaintText] = useState('');
  const [orderId, setOrderId] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeCase, setActiveCase] = useState<CaseFile | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState('');

  const config = TENANT_CONFIGS[clientId];

  const samplePrompts = {
    quickcart: [
      { label: 'Double Charge ($42.50)', text: 'I noticed two identical charges of $42.50 on my credit card for order QC-ORD-8901. Please refund the duplicate!', order: 'QC-ORD-8901' },
      { label: 'Delayed Delivery (5 days)', text: 'My guaranteed 2-day delivery order QC-ORD-8902 is 5 days delayed and still not here.', order: 'QC-ORD-8902' },
      { label: 'Lost / Missing Parcel', text: 'Tracking says delivered to porch for QC-ORD-8909, but I never received anything.', order: 'QC-ORD-8909' }
    ],
    telenet: [
      { label: '48h Broadband Outage', text: 'Our fiber broadband was completely down during the documented 48-hour outage on TN-ORD-8903. I request a service credit.', order: 'TN-ORD-8903' },
      { label: 'Unreturned Router Fee', text: 'You charged me an unreturned hardware fee for a router I already sent back.', order: '' },
      { label: 'Cancel Contract (VIP)', text: 'I am cancelling our enterprise fiber contract immediately due to ongoing speed issues.', order: '' }
    ],
    carelink: [
      { label: 'Duplicate Lab Copay ($50)', text: 'I was billed twice for my $50 copay for my routine lab blood test on CL-ORD-8904.', order: 'CL-ORD-8904' },
      { label: 'Adverse Drug Reaction (Safety)', text: 'I was billed twice for copay on CL-ORD-8904, and also I took the medicine prescribed and my throat is swelling and I have severe chest pain.', order: 'CL-ORD-8904' },
      { label: 'HIPAA Legal Lawsuit', text: 'CareLink billing staff shared my records improperly. My attorney will file a regulatory lawsuit.', order: '' }
    ]
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintText.trim()) return;

    setIsProcessing(true);
    try {
      const custId = clientId === 'quickcart' ? 'QC-CUST-103' : (clientId === 'telenet' ? 'TN-CUST-102' : 'CL-CUST-104');
      const result = await executePipeline(clientId, custId, complaintText, orderId || undefined);
      setActiveCase(result);
      if (onCaseCreated) onCaseCreated(result);
      setFeedbackSent(false);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFeedback = async (solved: boolean) => {
    if (!activeCase) return;
    await submitFeedback(activeCase.caseId, solved, feedbackComment || (solved ? 'Satisfied with resolution' : 'Issue still unresolved'));
    setFeedbackSent(true);
    if (!solved) {
      setActiveCase({ ...activeCase, status: 'REOPENED_ESCALATED' });
    }
  };

  const resetChat = () => {
    setActiveCase(null);
    setComplaintText('');
    setOrderId('');
    setFeedbackSent(false);
    setFeedbackComment('');
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <span>{config.clientName} Customer Support</span>
            <span className="text-xs font-normal text-slate-500">· Automated Help Assistant</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Powered by WideResolve Multi-Tenant Safety Engine
          </p>
        </div>
        {activeCase && (
          <button
            onClick={resetChat}
            className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Inquiry</span>
          </button>
        )}
      </div>

      {/* Body */}
      <div className="p-5 flex-1 overflow-y-auto space-y-4">
        {!activeCase ? (
          <div>
            <div className="mb-4">
              <p className="text-xs font-medium text-slate-700 mb-2">Try a realistic customer scenario:</p>
              <div className="flex flex-wrap gap-2">
                {samplePrompts[clientId].map((sp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setComplaintText(sp.text);
                      setOrderId(sp.order);
                    }}
                    className="text-xs text-left px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-800 transition-colors"
                  >
                    {sp.label}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Optional Order / Account ID
                </label>
                <input
                  type="text"
                  value={orderId}
                  onChange={e => setOrderId(e.target.value)}
                  placeholder={clientId === 'quickcart' ? 'e.g. QC-ORD-8901' : (clientId === 'telenet' ? 'e.g. TN-ORD-8903' : 'e.g. CL-ORD-8904')}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  How can we help you today?
                </label>
                <textarea
                  rows={4}
                  value={complaintText}
                  onChange={e => setComplaintText(e.target.value)}
                  placeholder="Describe your issue with full details..."
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900"
                />
                <p className="text-xs text-slate-500 mt-1">
                  PII such as phone, card, and email will be automatically redacted before processing.
                </p>
              </div>

              <button
                type="submit"
                disabled={isProcessing || !complaintText.trim()}
                className="w-full py-2.5 px-4 bg-slate-900 text-white text-xs font-medium rounded-lg hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing through WideResolve Pipeline...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit Complaint</span>
                  </>
                )}
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Customer Message Bubble */}
            <div className="flex justify-end">
              <div className="max-w-[85%] bg-slate-100 text-slate-900 rounded-xl rounded-tr-sm p-3 text-xs">
                <p className="font-semibold text-slate-700 text-xs mb-1">Your Message:</p>
                <p>{activeCase.rawComplaint}</p>
                {activeCase.orderId && (
                  <p className="text-xs text-slate-500 mt-1">Order Ref: {activeCase.orderId}</p>
                )}
              </div>
            </div>

            {/* System Resolution Bubble */}
            <div className="flex justify-start">
              <div className="max-w-[90%] bg-slate-50 border border-slate-200 rounded-xl rounded-tl-sm p-4 text-xs space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-semibold text-slate-900">
                    {activeCase.status === 'AUTO_RESOLVED' && (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Resolution Approved (Auto-Resolved)</span>
                      </>
                    )}
                    {activeCase.status === 'WAITING_APPROVAL' && (
                      <>
                        <Clock className="w-4 h-4 text-amber-600" />
                        <span>Queued for Supervisor Approval</span>
                      </>
                    )}
                    {activeCase.status === 'ESCALATED' && (
                      <>
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                        <span>Escalated to Senior Team</span>
                      </>
                    )}
                    {activeCase.status === 'REOPENED_ESCALATED' && (
                      <>
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                        <span>Case Reopened & Escalated</span>
                      </>
                    )}
                  </div>
                  <span className="font-mono text-xs text-slate-500">{activeCase.caseId}</span>
                </div>

                <p className="text-slate-800 leading-relaxed">
                  {activeCase.proposedResolution.customerMessage}
                </p>

                {activeCase.proposedResolution.amount > 0 && (
                  <div className="p-2.5 bg-white border border-slate-200 rounded-lg flex items-center justify-between text-xs">
                    <span className="text-slate-600 font-medium">Disbursed / Credit Amount:</span>
                    <span className="font-bold text-slate-900 font-mono text-sm">
                      ${activeCase.proposedResolution.amount.toFixed(2)}
                    </span>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                  <span>Policy Citation: {activeCase.proposedResolution.policyCitation}</span>
                  <span className="font-mono">Confidence: {(activeCase.escalationDecision.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Satisfaction Feedback Section */}
            {!feedbackSent ? (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <p className="text-xs font-medium text-slate-800 mb-2">Did this resolve your concern?</p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleFeedback(true)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>Yes, Resolved</span>
                  </button>
                  <button
                    onClick={() => handleFeedback(false)}
                    className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-800 rounded text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>No, Reopen & Escalate</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-2.5 bg-slate-100 rounded-lg text-xs text-slate-600">
                Feedback recorded into audit chain. Thank you!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
