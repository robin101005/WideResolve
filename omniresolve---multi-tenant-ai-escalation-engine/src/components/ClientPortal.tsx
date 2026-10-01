import React, { useState } from 'react';
import { ClientId, CaseFile, CaseStatus } from '../lib/types';
import { TENANT_CONFIGS, getCases, MOCK_CUSTOMERS } from '../lib/mockEngine';
import { ChatWidget } from './ChatWidget';
import { AgentTraceModal } from './AgentTraceModal';
import { CaseBriefModal } from './CaseBriefModal';
import {
  Shield,
  Layers,
  Sliders,
  MessageSquare,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  BookOpen
} from 'lucide-react';

interface ClientPortalProps {
  currentClient: ClientId;
  onSelectClient: (id: ClientId) => void;
}

export const ClientPortal: React.FC<ClientPortalProps> = ({ currentClient, onSelectClient }) => {
  const [activeTab, setActiveTab] = useState<'cases' | 'widget' | 'settings'>('cases');
  const [statusFilter, setStatusFilter] = useState<'ALL' | CaseStatus>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTraceCase, setSelectedTraceCase] = useState<CaseFile | null>(null);
  const [selectedBriefCase, setSelectedBriefCase] = useState<CaseFile | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const config = TENANT_CONFIGS[currentClient];
  const allCases = getCases(currentClient);

  const filteredCases = allCases.filter(c => {
    if (statusFilter !== 'ALL' && c.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = c.caseId.toLowerCase().includes(q);
      const matchOrder = c.orderId?.toLowerCase().includes(q) || false;
      const matchText = c.rawComplaint.toLowerCase().includes(q);
      return matchId || matchOrder || matchText;
    }
    return true;
  });

  const autoResolvedCount = allCases.filter(c => c.status === 'AUTO_RESOLVED').length;
  const waitingApprovalCount = allCases.filter(c => c.status === 'WAITING_APPROVAL').length;
  const escalatedCount = allCases.filter(c => c.status === 'ESCALATED' || c.status === 'REOPENED_ESCALATED').length;

  return (
    <div className="space-y-6">
      {/* Top Client Tenant Switcher Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-900 text-white flex items-center justify-center font-bold text-base">
            {config.clientName.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900">{config.clientName} Client Portal</h1>
              <span className="text-xs text-slate-500 font-normal">· Multi-Tenant Isolated View</span>
            </div>
            <p className="text-xs text-slate-500">
              Industry: <span className="text-slate-700 font-medium">{config.industry}</span> · Autonomous Cap: <span className="font-mono text-slate-700 font-semibold">${config.authorityLimit.toFixed(2)}</span>
            </p>
          </div>
        </div>

        {/* Tenant Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Switch Tenant:</span>
          {(['quickcart', 'telenet', 'carelink'] as ClientId[]).map(id => (
            <button
              key={id}
              onClick={() => onSelectClient(id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                currentClient === id
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              {TENANT_CONFIGS[id].clientName}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 pb-px">
        <button
          onClick={() => setActiveTab('cases')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            activeTab === 'cases'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4" />
            <span>Customer Escalations ({allCases.length})</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('widget')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            activeTab === 'widget'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            <span>Embeddable Customer Widget Preview</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer border-b-2 ${
            activeTab === 'settings'
              ? 'border-slate-900 text-slate-900 bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4" />
            <span>YAML Config & Policy Rules</span>
          </div>
        </button>
      </div>

      {/* Tab 1: Case Management List */}
      {activeTab === 'cases' && (
        <div className="space-y-4">
          {/* Quick Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs text-slate-500 block">Total Escalation Volume</span>
              <span className="text-2xl font-bold font-mono text-slate-900 mt-1 block">
                {allCases.length}
              </span>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs text-emerald-600 font-medium block">Auto-Resolved</span>
              <span className="text-2xl font-bold font-mono text-emerald-700 mt-1 block">
                {autoResolvedCount}
              </span>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs text-amber-600 font-medium block">Waiting Approval</span>
              <span className="text-2xl font-bold font-mono text-amber-700 mt-1 block">
                {waitingApprovalCount}
              </span>
            </div>
            <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
              <span className="text-xs text-rose-600 font-medium block">Human Escalated</span>
              <span className="text-2xl font-bold font-mono text-rose-700 mt-1 block">
                {escalatedCount}
              </span>
            </div>
          </div>

          {/* Filters & Search */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search by Case ID, Order ID, or text..."
                className="w-full text-xs pl-9 pr-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-slate-900"
              />
            </div>

            {/* Status Segmented Control */}
            <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg text-xs">
              {(['ALL', 'AUTO_RESOLVED', 'WAITING_APPROVAL', 'ESCALATED'] as const).map(st => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                    statusFilter === st
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {st === 'ALL' ? 'All' : st.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Cases Table */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase text-[10px] tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Case ID</th>
                    <th className="py-3 px-4">Customer & Order</th>
                    <th className="py-3 px-4">Issue Summary</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4">Payout</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredCases.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400 italic">
                        No customer complaints found matching criteria. Use the Chat Widget to submit one!
                      </td>
                    </tr>
                  ) : (
                    filteredCases.map(c => (
                      <tr key={c.caseId} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-slate-900 whitespace-nowrap">
                          {c.caseId}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-900 block">{c.customerProfile?.name || c.customerId}</span>
                          <span className="font-mono text-slate-400 text-[11px]">{c.orderId || 'No Order Ref'}</span>
                        </td>
                        <td className="py-3 px-4 max-w-xs">
                          <span className="font-medium text-slate-900 block">{c.intent.issueType}</span>
                          <span className="text-slate-500 truncate block text-[11px]">{c.rawComplaint}</span>
                        </td>
                        <td className="py-3 px-4 font-mono font-medium">
                          {(c.escalationDecision.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                          {c.proposedResolution.amount > 0 ? `$${c.proposedResolution.amount.toFixed(2)}` : '—'}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium ${
                            c.status === 'AUTO_RESOLVED' || c.status === 'APPROVED_AND_RESOLVED'
                              ? 'bg-emerald-50 text-emerald-700'
                              : c.status === 'WAITING_APPROVAL'
                              ? 'bg-amber-50 text-amber-700'
                              : 'bg-rose-50 text-rose-700'
                          }`}>
                            {c.status === 'AUTO_RESOLVED' && <CheckCircle2 className="w-3.5 h-3.5" />}
                            {c.status === 'WAITING_APPROVAL' && <Clock className="w-3.5 h-3.5" />}
                            {(c.status === 'ESCALATED' || c.status === 'REOPENED_ESCALATED') && <AlertTriangle className="w-3.5 h-3.5" />}
                            <span>{c.status.replace(/_/g, ' ')}</span>
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                          <button
                            onClick={() => setSelectedTraceCase(c)}
                            className="px-2.5 py-1 border border-slate-200 hover:bg-slate-100 text-slate-800 rounded text-xs font-medium transition-colors cursor-pointer"
                          >
                            Trace
                          </button>
                          {c.caseBrief && (
                            <button
                              onClick={() => setSelectedBriefCase(c)}
                              className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium transition-colors cursor-pointer"
                            >
                              Case Brief
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Embeddable Customer Chat Widget Preview */}
      {activeTab === 'widget' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-4 text-xs text-slate-600">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                <span>Integration Instructions</span>
              </h3>
              <p>
                This chat assistant widget is embeddable on {config.clientName}'s mobile app or website via a single lightweight script tag.
              </p>
              <div className="p-3 bg-slate-900 text-slate-200 rounded-lg font-mono text-[11px] overflow-x-auto">
                <code>{`<script src="https://omni-resolve.io/v1/widget.js"\n  data-tenant="${config.clientId}"\n  data-theme="minimal">\n</script>`}</code>
              </div>
              <p>
                All complaints submitted through this interface are sanitized for PII, evaluated against the client's authority limits (<strong className="text-slate-900">${config.authorityLimit.toFixed(2)}</strong>), and strictly isolated to {config.clientName}'s database.
              </p>
            </div>
          </div>

          <div className="lg:col-span-2 min-h-[500px]">
            <ChatWidget
              clientId={currentClient}
              onCaseCreated={() => setRefreshTrigger(prev => prev + 1)}
            />
          </div>
        </div>
      )}

      {/* Tab 3: YAML Config & Policy Inspector */}
      {activeTab === 'settings' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* Config Pack Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">Tenant Configuration Pack (configs/{config.clientId}.yaml)</h3>
              <span className="font-mono text-xs text-slate-400">Read-Only</span>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Tenant ID:</span>
                <span className="font-mono font-bold text-slate-900">{config.clientId}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Autonomous Authority Cap:</span>
                <span className="font-mono font-bold text-slate-900">${config.authorityLimit.toFixed(2)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Confidence Auto-Resolve Cutoff:</span>
                <span className="font-mono font-bold text-slate-900">{(config.confidenceThreshold * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Configured Tone:</span>
                <span className="text-slate-800 text-right">{config.tone}</span>
              </div>
            </div>

            <div>
              <span className="font-semibold text-slate-900 block mb-2">Deterministic Hard Escalation Overrides:</span>
              <ul className="list-disc pl-4 space-y-1 text-slate-700">
                {config.hardEscalationRules.map((rule, idx) => (
                  <li key={idx}>{rule}</li>
                ))}
              </ul>
            </div>

            <div>
              <span className="font-semibold text-slate-900 block mb-2">Allowed Data Access Tools:</span>
              <div className="flex flex-wrap gap-1.5">
                {config.allowedTools.map((tool, idx) => (
                  <span key={idx} className="font-mono px-2 py-1 bg-slate-100 text-slate-800 rounded text-[11px]">
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Active Policies Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-900">Active Policy Clauses (policies/{config.clientId}_policies.md)</h3>
              <span className="font-mono text-xs text-slate-400">RAG Corpus</span>
            </div>

            <div className="space-y-3">
              {currentClient === 'quickcart' && (
                <>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Refund §1.1: Double Charges</h4>
                    <p className="text-slate-600 text-[11px]">Automatic full refund for gateway glitches without requiring merchandise return.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Delivery §2.1: Expedited Transit Delays</h4>
                    <p className="text-slate-600 text-[11px]">$10.00 store courtesy credit when delivery is &gt;48 hours late past SLA.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Delivery §2.2: Lost in Transit / Dispute</h4>
                    <p className="text-slate-600 text-[11px]">Automated courtesy replacement capped at $50.00; higher amounts require manager approval.</p>
                  </div>
                </>
              )}

              {currentClient === 'telenet' && (
                <>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Billing §1.1: Erroneous Equipment Charges</h4>
                    <p className="text-slate-600 text-[11px]">Reversal of unreturned equipment fee after warehouse drop-off receipt confirmation.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Outage §2.2: Major Outages (&gt;36 Hours)</h4>
                    <p className="text-slate-600 text-[11px]">Flat $35.00 courtesy service credit for verified continuous network blackouts upon supervisor review.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Limit §3.1: Compensation Limits</h4>
                    <p className="text-slate-600 text-[11px]">Autonomous credit ceiling of $40.00. TeleNet credits require supervisor NOC log sign-off.</p>
                  </div>
                </>
              )}

              {currentClient === 'carelink' && (
                <>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Billing §1.1: Duplicate Copay Charges</h4>
                    <p className="text-slate-600 text-[11px]">Immediate refund of secondary copay on single clinic encounter to patient's HSA or card.</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <h4 className="font-semibold text-slate-900 mb-0.5">Scheduling §2.1: Cancellation Fee Waiver</h4>
                    <p className="text-slate-600 text-[11px]">Automatic waiver of cancellation fees caused by clinic doctor scheduling conflicts.</p>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
                    <h4 className="font-semibold text-rose-900 mb-0.5">Safety §4.2: Clinical Safety Firewall (MANDATORY ESCALATION)</h4>
                    <p className="text-rose-800 text-[11px]">Any symptom, pain, prescription, or medication mention immediately routes to registered nursing staff.</p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <AgentTraceModal
        caseFile={selectedTraceCase}
        onClose={() => setSelectedTraceCase(null)}
      />

      <CaseBriefModal
        caseFile={selectedBriefCase}
        onClose={() => setSelectedBriefCase(null)}
        onActionComplete={() => setRefreshTrigger(prev => prev + 1)}
      />
    </div>
  );
};
