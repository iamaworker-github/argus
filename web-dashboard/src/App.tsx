import { useBackend } from './hooks/useBackend';
import HeaderBar from './components/HeaderBar';
import LeftPanel from './components/LeftPanel';
import OperationPipeline from './components/OperationPipeline';
import AgentLog from './components/AgentLog';
import ActivityFeed from './components/ActivityFeed';
import AttackGraph from './components/AttackGraph';
import KeyFindings from './components/KeyFindings';
import RightPanel from './components/RightPanel';
import FooterBar from './components/FooterBar';

const S = {
  root: {
    width: '100vw',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    background: '#080c08',
    userSelect: 'none' as const,
    fontFamily: "'JetBrains Mono', 'Courier New', monospace",
  },
  main: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
    minHeight: 0,
  },
  center: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    minWidth: 0,
  },
  centerBody: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
    minHeight: 0,
  },
  leftCol: {
    width: '46%',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    borderRight: '1px solid #1a2a1a',
  },
  agentPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    minHeight: 0,
    margin: '3px 3px 0 3px',
    border: '1px solid #1e3a1e',
    background: '#090e09',
  },
  activityWrap: {
    flexShrink: 0,
    margin: '3px 3px 3px 3px',
    border: '1px solid #1a2a1a',
    background: '#090e09',
  },
  rightCol: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    minWidth: 0,
  },
  graphWrap: {
    flex: 1,
    overflow: 'hidden',
    minHeight: 0,
    margin: '3px 3px 0 0',
    border: '1px solid #1a2a1a',
  },
  findingsWrap: {
    flexShrink: 0,
    margin: '3px 3px 3px 0',
    border: '1px solid #1a2a1a',
    background: '#090e09',
  },
};

export default function App() {
  const { state, selectedAgent, setSelectedAgent } = useBackend();

  return (
    <div style={S.root}>
      {/* CRT effects */}
      <div className="scanlines" />
      <div className="vignette" />

      {/* ── HEADER ── */}
      <HeaderBar state={state} />

      {/* ── BODY ── */}
      <div style={S.main}>

        {/* LEFT SIDEBAR */}
        <LeftPanel
          state={state}
          selectedAgent={selectedAgent}
          onSelectAgent={setSelectedAgent}
        />

        {/* CENTER */}
        <div style={S.center}>
          <OperationPipeline stages={state.pipeline} />

          <div style={S.centerBody}>
            {/* Agent log + activity */}
            <div style={S.leftCol}>
              <div style={S.agentPanel}>
                <AgentLog
                  agentName={state.activeAgentName}
                  agentTime={state.activeAgentTime}
                  logs={state.logs}
                  thinkingLines={state.thinkingLines}
                  tokensUsed={state.tokensUsed}
                />
              </div>
              <div style={S.activityWrap}>
                <ActivityFeed activities={state.activities} verbosity="High" />
              </div>
            </div>

            {/* Attack graph + findings */}
            <div style={S.rightCol}>
              <div style={S.graphWrap}>
                <AttackGraph nodes={state.nodes} edges={state.edges} />
              </div>
              <div style={S.findingsWrap}>
                <KeyFindings
                  findings={state.findings}
                  riskScore={state.riskScore}
                  riskLabel={state.riskLabel}
                />
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT SIDEBAR */}
        <RightPanel state={state} />
      </div>

      {/* ── FOOTER ── */}
      <FooterBar />
    </div>
  );
}
