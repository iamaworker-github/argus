import { useState, useCallback } from 'react';
import type { Toast } from './types';

import { useBackend } from './hooks/useBackend';

import TopBar from './components/TopBar';
import LeftPanel from './components/LeftPanel';
import PipelineBar from './components/PipelineBar';
import UnifiedTimeline from './components/UnifiedTimeline';
import ThinkingPanel from './components/ThinkingPanel';
import RightPanel from './components/RightPanel';
import BottomBar from './components/BottomBar';
import ToastNotification from './components/ToastNotification';
import ChatPanel from './components/ChatPanel';

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  'Plan Agent': 'AI Planning Agent',
};

function getAgentDisplayName(name: string): string {
  return AGENT_DISPLAY_NAMES[name] || name;
}

export default function App() {
  const sim = useBackend();
  const [filterAgent, setFilterAgent] = useState('all');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [chatOpen, setChatOpen] = useState(false);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const handlePause = useCallback((id: string) => {
    sim.sendCommand('agent_pause', { agent_id: id });
  }, [sim]);

  const handleResume = useCallback((id: string) => {
    sim.sendCommand('agent_resume', { agent_id: id });
  }, [sim]);

  const handleKill = useCallback((id: string) => {
    sim.sendCommand('agent_kill', { agent_id: id });
  }, [sim]);

  const handleExport = useCallback(() => {
    const report = {
      target: sim.target,
      session: sim.sessionId,
      timestamp: new Date().toISOString(),
      findings: sim.findings,
      pipeline: sim.pipelineStages,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `argus-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [sim.target, sim.sessionId, sim.findings, sim.pipelineStages]);

  const handleCommand = useCallback((cmd: string) => {
    sim.requestScan(cmd, 'pentest');
  }, [sim]);

  const currentAgent = sim.agents.find((a) => a.status === 'Running') || null;
  const agentDisplayName = currentAgent ? getAgentDisplayName(currentAgent.name) : null;

  const sessionMetrics = {
    commandsExecuted: sim.commandCount,
    dataCollected: sim.findings.length > 0 ? sim.findings.length : 0,
    findings: sim.findings.length,
    vulnerabilities: sim.findings.filter((f) => f.severity === 'HIGH' || f.severity === 'CRITICAL').length,
    timeElapsed: sim.elapsed,
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-300 overflow-hidden select-none">
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #18181b; }
        ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 2px; }
        ::-webkit-scrollbar-thumb:hover { background: #52525b; }
      `}</style>

      <ToastNotification toasts={toasts} onDismiss={dismissToast} />
      <TopBar elapsed={sim.elapsed} sessionId={sim.sessionId} target={sim.target} />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <LeftPanel
          agents={sim.agents}
          cpu={Math.round(sim.cpu)}
          mem={Math.round(sim.mem)}
          net={Math.round(sim.net)}
          tokens={sim.tokens}
          credits={sim.credits}
          elapsed={sim.elapsed}
          llmModel={sim.llmModel}
          riskProfile={sim.riskProfile}
          maxParallel={sim.maxParallel}
          safeMode={sim.safeMode}
          agentStatus={sim.agentStatus}
          onPause={handlePause}
          onResume={handleResume}
          onKill={handleKill}
        />

        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <PipelineBar stages={sim.pipelineStages} />

          <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative">
            <div className="flex-1 min-h-0 overflow-hidden">
              <UnifiedTimeline
                events={sim.timeline}
                agentName={agentDisplayName || (sim.agentStatus === 'IDLE' ? 'System' : sim.agentStatus)}
                agentStatus={currentAgent?.status || (sim.agentStatus === 'IDLE' ? 'Idle' : 'Running')}
                elapsed={sim.elapsed}
                filterAgent={filterAgent}
                filterSeverity={filterSeverity}
                onFilterAgentChange={setFilterAgent}
                onFilterSeverityChange={setFilterSeverity}
                agents={sim.agents}
              />
            </div>

            <ThinkingPanel
              agentName={agentDisplayName || (sim.agentStatus === 'IDLE' ? 'System' : sim.agentStatus)}
              thought={sim.currentThought}
              lastThought={sim.lastThought}
              thinkingLines={sim.thinkingLines}
              tokens={`${(sim.tokens / 1000).toFixed(1)}M`}
            />
          </div>
          </div>

        <RightPanel
          target={sim.target}
          mode={sim.mode}
          ipAddress={sim.targetIP}
          openPorts={sim.openPorts}
          subdomains={sim.subdomains}
          technologies={sim.technologiesCount}
          attackSurface={sim.attackSurface}
          topTech={sim.topTech}
          recentDiscoveries={sim.recentDiscoveries}
          findings={sim.findings}
          metrics={sessionMetrics}
          riskScore={sim.riskScore}
          riskLevel={sim.riskLevel}
          nodes={sim.graphNodes}
          edges={sim.graphEdges}
          onExport={handleExport}
        />
      </div>

      <div className="relative">
        <div className="absolute bottom-0 right-0 z-40 mb-1 mr-2">
          <button
            onClick={() => setChatOpen(!chatOpen)}
            className="text-[11px] font-mono text-zinc-400 hover:text-zinc-200 border border-zinc-700 hover:border-zinc-500 px-2 py-0.5 rounded transition-colors bg-zinc-900"
          >
            {chatOpen ? 'Close Chat' : 'AI Chat'}
          </button>
        </div>
        <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
      </div>
      <BottomBar onCommand={handleCommand} shortcuts={['? Help', 'Tab Complete', 'Ctrl+K Commands', 'Ctrl+D Exit']} />
    </div>
  );
}
