import React, { useState, useEffect } from 'react';
import { ClientId } from './lib/types';
import { seedGoldenCases } from './lib/mockEngine';
import { ClientPortal } from './components/ClientPortal';
import { MobileOpsConsole } from './components/MobileOpsConsole';
import { DemoWalkthrough } from './components/DemoWalkthrough';
import { EvaluationBench } from './components/EvaluationBench';
import { WorkflowDiagram } from './components/WorkflowDiagram';
import {
  ShieldCheck,
  Building2,
  Smartphone,
  Sparkles,
  BarChart2,
  FileCode2,
  GitBranch,
  Layers,
  FileText
} from 'lucide-react';

export default function App() {
  const [activeView, setActiveView] = useState<'client' | 'admin' | 'workflow' | 'demo' | 'eval'>('client');
  const [currentClient, setCurrentClient] = useState<ClientId>('quickcart');

  useEffect(() => {
    // Seed golden cases matching Hackathon Problem Statement 07
    seedGoldenCases();
  }, []);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 px-6 py-3 flex items-center justify-between shadow-xs">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-xs">
            WR
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-tight text-slate-900">
                WideResolve
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                Widesoftech
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              AI Customer Escalation Agent · Problem Statement 07
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-2 sm:gap-5 text-xs font-semibold text-slate-600">
          <button
            onClick={() => setActiveView('client')}
            className={`transition-colors cursor-pointer py-1.5 px-2 rounded-md ${
              activeView === 'client' ? 'bg-slate-900 text-white font-bold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Client Portal
          </button>
          <button
            onClick={() => setActiveView('admin')}
            className={`transition-colors cursor-pointer py-1.5 px-2 rounded-md ${
              activeView === 'admin' ? 'bg-slate-900 text-white font-bold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Admin Portal (Widesoftech)
          </button>
          <button
            onClick={() => setActiveView('workflow')}
            className={`transition-colors cursor-pointer py-1.5 px-2 rounded-md ${
              activeView === 'workflow' ? 'bg-slate-900 text-white font-bold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Detective Workflow & Agents
          </button>
          <button
            onClick={() => setActiveView('demo')}
            className={`transition-colors cursor-pointer py-1.5 px-2 rounded-md ${
              activeView === 'demo' ? 'bg-slate-900 text-white font-bold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Example Cases Demo
          </button>
          <button
            onClick={() => setActiveView('eval')}
            className={`transition-colors cursor-pointer py-1.5 px-2 rounded-md ${
              activeView === 'eval' ? 'bg-slate-900 text-white font-bold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Evaluation Bench
          </button>
        </nav>

        {/* Status & Quick Action */}
        <div className="hidden lg:flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-medium px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-bold">Live AI: Google Gemini 3.8 Flash</span>
          </div>

          <button
            onClick={() => setActiveView('demo')}
            className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors whitespace-nowrap cursor-pointer shadow-xs"
          >
            Run Example Cases
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeView === 'client' && (
          <ClientPortal
            currentClient={currentClient}
            onSelectClient={setCurrentClient}
          />
        )}

        {activeView === 'admin' && (
          <MobileOpsConsole />
        )}

        {activeView === 'workflow' && (
          <WorkflowDiagram />
        )}

        {activeView === 'demo' && (
          <DemoWalkthrough />
        )}

        {activeView === 'eval' && (
          <EvaluationBench />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-4 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2 mt-auto">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700">Widesoftech WideResolve</span>
          <span>·</span>
          <span>B2B Multi-Tenant Client Isolation</span>
          <span>·</span>
          <span>Evidence-Based Contract SLA Resolution</span>
        </div>
        <div>
          <span>Clients: QuickCart (E-Commerce) · TeleNet (Telecom) · CareLink (Healthcare)</span>
        </div>
      </footer>
    </div>
  );
}
