import React, { useState, useEffect } from 'react';
import { CaseFile, AuditRecord } from '../lib/types';
import {
  getCases,
  getAuditRecords,
  verifyAuditChain,
  simulateTamper,
  resetAuditChain,
  approveCase,
  rejectCase
} from '../lib/mockEngine';
import { CaseBriefModal } from './CaseBriefModal';
import { AgentTraceModal } from './AgentTraceModal';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Lock,
  RefreshCw,
  AlertTriangle,
  FileText,
  Search,
  Check,
  Smartphone,
  Laptop
} from 'lucide-react';

export const MobileOpsConsole: React.FC = () => {
  const [cases, setCases] = useState<CaseFile[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [verifyResult, setVerifyResult] = useState<{ valid: boolean; message: string; brokenAtId?: number } | null>(null);
  const [selectedCase, setSelectedCase] = useState<CaseFile | null>(null);
  const [traceCase, setTraceCase] = useState<CaseFile | null>(null);
  const [viewMode, setViewMode] = useState<'desktop' | 'mobile'>('desktop');
  const [filterTab, setFilterTab] = useState<'queue' | 'audit' | 'all'>('queue');
  const [isVerifying, setIsVerifying] = useState(false);

  const reloadData = () => {
    setCases(getCases());
    setAuditLogs(getAuditRecords());
  };

  useEffect(() => {
    reloadData();
  }, []);

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const res = await verifyAuditChain();
      setVerifyResult(res);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    if (auditLogs.length > 1) {
      simulateTamper(auditLogs[1].id);
      reloadData();
      await handleVerifyChain();
    }
  };

  const handleResetAudit = async () => {
    await resetAuditChain();
    reloadData();
    setVerifyResult(null);
  };

  const queueCases = cases.filter(c => c.status === 'WAITING_APPROVAL' || c.status === 'ESCALATED' || c.status === 'REOPENED_ESCALATED');

  return (
    <div className={`space-y-6 ${viewMode === 'mobile' ? 'max-w-md mx-auto border-x border-slate-300 min-h-screen bg-slate-50 p-3 shadow-2xl rounded-2xl my-4' : ''}`}>
      {/* Top Header */}
      <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-mono font-semibold text-emerald-400 uppercase tracking-wider">Internal Operations</span>
            <span className="text-slate-500">·</span>
            <span className="text-xs text-slate-300">All-Client Escalation Center</span>
          </div>
          <h1 className="text-lg font-bold text-white mt-1">WideResolve Admin & Escalation Console</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Cross-tenant supervisor workflow, human-in-the-loop approvals & cryptographic audit verification.
          </p>
        </div>

        {/* Viewport & Refresh controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setViewMode('desktop')}
              className={`p-1.5 rounded transition-colors cursor-pointer ${
                viewMode === 'desktop' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Desktop View"
            >
              <Laptop className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('mobile')}
              className={`p-1.5 rounded transition-colors cursor-pointer ${
                viewMode === 'mobile' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Mobile App Simulation (React Native Layout)"
            >
              <Smartphone className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={reloadData}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs transition-colors cursor-pointer"
            title="Refresh Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Cross-Tenant Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <span className="text-[11px] text-slate-500 block">Pending Approvals</span>
          <span className="text-xl font-bold font-mono text-amber-600 mt-0.5 block">
            {cases.filter(c => c.status === 'WAITING_APPROVAL').length}
          </span>
        </div>

        <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <span className="text-[11px] text-slate-500 block">Active Escalations</span>
          <span className="text-xl font-bold font-mono text-rose-600 mt-0.5 block">
            {cases.filter(c => c.status === 'ESCALATED' || c.status === 'REOPENED_ESCALATED').length}
          </span>
        </div>

        <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <span className="text-[11px] text-slate-500 block">Autonomous Resolves</span>
          <span className="text-xl font-bold font-mono text-emerald-600 mt-0.5 block">
            {cases.filter(c => c.status === 'AUTO_RESOLVED' || c.status === 'APPROVED_AND_RESOLVED').length}
          </span>
        </div>

        <div className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm">
          <span className="text-[11px] text-slate-500 block">Audit Chain Blocks</span>
          <span className="text-xl font-bold font-mono text-slate-900 mt-0.5 block">
            {auditLogs.length}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 pb-px">
        <button
          onClick={() => setFilterTab('queue')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            filterTab === 'queue'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-600" />
            <span>Escalation & Approval Queue ({queueCases.length})</span>
          </div>
        </button>

        <button
          onClick={() => setFilterTab('audit')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            filterTab === 'audit'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-indigo-600" />
            <span>Hash-Chained Audit Ledger ({auditLogs.length})</span>
          </div>
        </button>

        <button
          onClick={() => setFilterTab('all')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            filterTab === 'all'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>All Tenant Cases ({cases.length})</span>
          </div>
        </button>
      </div>

      {/* Tab: Escalation Queue */}
      {filterTab === 'queue' && (
        <div className="space-y-4">
          {queueCases.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400 italic">
              All queues clear! Zero pending approvals or escalations.
            </div>
          ) : (
            queueCases.map(c => (
              <div
                key={c.caseId}
                className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm hover:border-slate-300 transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-900">{c.caseId}</span>
                      <span className="text-xs text-slate-300">·</span>
                      <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                        {c.clientId}
                      </span>
                      <span className="text-xs text-slate-300">·</span>
                      <span className="text-xs text-slate-500 font-medium">{c.customerProfile?.name}</span>
                    </div>
                    <p className="text-xs font-semibold text-slate-900 mt-1">
                      {c.intent.issueType}
                    </p>
                  </div>

                  <span className={`px-2.5 py-1 rounded text-xs font-medium shrink-0 ${
                    c.status === 'WAITING_APPROVAL' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'
                  }`}>
                    {c.status.replace(/_/g, ' ')}
                  </span>
                </div>

                <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 font-mono">
                  "{c.rawComplaint}"
                </p>

                {/* Hard rules violated if any */}
                {c.escalationDecision.hardRulesTriggered.length > 0 && (
                  <div className="p-2.5 bg-rose-50/70 border border-rose-200/70 rounded-lg text-rose-800 text-[11px]">
                    <strong className="block mb-0.5">Critical Gate Trigger:</strong>
                    {c.escalationDecision.hardRulesTriggered[0]}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-4 text-slate-600">
                    <span>Proposed: <strong className="text-slate-900">{c.proposedResolution.proposedAction}</strong></span>
                    {c.proposedResolution.amount > 0 && (
                      <span>Amount: <strong className="text-slate-900 font-mono">${c.proposedResolution.amount.toFixed(2)}</strong></span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setTraceCase(c)}
                      className="px-2.5 py-1 text-xs text-slate-700 border border-slate-200 rounded hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                      View Trace
                    </button>
                    <button
                      onClick={() => setSelectedCase(c)}
                      className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium transition-colors cursor-pointer"
                    >
                      Case Brief & Action
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab: Cryptographic Audit Ledger */}
      {filterTab === 'audit' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Lock className="w-4 h-4 text-indigo-600" />
                <span>SHA-256 Hash-Chained Audit Ledger</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Each block seals: sha256(previous_hash + timestamp + case_id + action + payload)
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleVerifyChain}
                disabled={isVerifying}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
              >
                {isVerifying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                <span>Verify Chain</span>
              </button>

              <button
                onClick={handleSimulateTamper}
                className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-medium rounded-lg transition-colors cursor-pointer"
                title="Corrupt row #2 to demonstrate cryptographic tamper detection"
              >
                Simulate Tamper
              </button>

              <button
                onClick={handleResetAudit}
                className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                Reset Chain
              </button>
            </div>
          </div>

          {/* Verification Status Banner */}
          {verifyResult && (
            <div className={`p-3.5 rounded-lg border text-xs flex items-start gap-2.5 ${
              verifyResult.valid ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}>
              {verifyResult.valid ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-semibold">{verifyResult.valid ? 'Chain Integrity Intact' : 'TAMPER DETECTED'}</p>
                <p className="mt-0.5">{verifyResult.message}</p>
              </div>
            </div>
          )}

          {/* Audit Rows */}
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[10px] uppercase">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Tenant</th>
                  <th className="py-2.5 px-3">Case ID</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3 font-mono">Previous Hash</th>
                  <th className="py-2.5 px-3 font-mono">Current Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
                {auditLogs.map((log, idx) => (
                  <tr key={log.id} className="hover:bg-slate-50/70">
                    <td className="py-2.5 px-3 font-bold text-slate-900">{log.id}</td>
                    <td className="py-2.5 px-3 uppercase text-[10px] font-sans font-semibold text-slate-600">{log.clientId}</td>
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-900">{log.caseId}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-800 text-[10px] font-medium">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 truncate max-w-[140px]" title={log.previousHash}>
                      {log.previousHash.slice(0, 16)}...
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-indigo-700 truncate max-w-[140px]" title={log.currentHash}>
                      {log.currentHash.slice(0, 16)}...
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: All Cases */}
      {filterTab === 'all' && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[10px] tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Tenant</th>
                  <th className="py-3 px-4">Issue</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {cases.map(c => (
                  <tr key={c.caseId} className="hover:bg-slate-50/70">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{c.caseId}</td>
                    <td className="py-3 px-4 uppercase text-slate-500 font-semibold text-[11px]">{c.clientId}</td>
                    <td className="py-3 px-4">{c.intent.issueType}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                        c.status === 'AUTO_RESOLVED' || c.status === 'APPROVED_AND_RESOLVED'
                          ? 'bg-emerald-50 text-emerald-700'
                          : c.status === 'WAITING_APPROVAL'
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-rose-50 text-rose-700'
                      }`}>
                        {c.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => setTraceCase(c)}
                        className="px-2.5 py-1 border border-slate-200 rounded hover:bg-slate-100 text-xs font-medium cursor-pointer"
                      >
                        Trace
                      </button>
                      {c.caseBrief && (
                        <button
                          onClick={() => setSelectedCase(c)}
                          className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium cursor-pointer"
                        >
                          Brief
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modals */}
      <CaseBriefModal
        caseFile={selectedCase}
        onClose={() => setSelectedCase(null)}
        onActionComplete={reloadData}
      />

      <AgentTraceModal
        caseFile={traceCase}
        onClose={() => setTraceCase(null)}
      />
    </div>
  );
};
