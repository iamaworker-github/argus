import type { SystemState } from '../types';

interface Props {
  state: SystemState;
  selectedAgent: string;
  onSelectAgent: (id: string) => void;
}

function EagleLogo() {
  return (
    <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
      {/* Hexagon border */}
      <polygon
        points="30,3 55,17 55,43 30,57 5,43 5,17"
        fill="#080f08"
        stroke="#00ff88"
        strokeWidth="1.5"
      />
      {/* Inner glow ring */}
      <polygon
        points="30,7 51,19 51,41 30,53 9,41 9,19"
        fill="none"
        stroke="#00440022"
        strokeWidth="4"
      />

      {/* Eagle body - stylized */}
      {/* Wings spread */}
      <path d="M15 28 C10 24 7 20 10 16 C14 18 18 22 22 26" fill="#00aa44" opacity="0.7"/>
      <path d="M45 28 C50 24 53 20 50 16 C46 18 42 22 38 26" fill="#00aa44" opacity="0.7"/>

      {/* Body */}
      <ellipse cx="30" cy="32" rx="8" ry="10" fill="#005522" opacity="0.8"/>

      {/* Head */}
      <circle cx="30" cy="20" r="8" fill="#00cc55" opacity="0.9"/>
      <circle cx="30" cy="20" r="6" fill="#004422"/>
      <circle cx="30" cy="20" r="5" fill="#00aa44" opacity="0.3"/>

      {/* Beak */}
      <path d="M35 20 L40 22 L35 23 Z" fill="#f0a500"/>
      <path d="M35 20 L40 21 L35 21.5 Z" fill="#c47f00"/>

      {/* Eye */}
      <circle cx="33" cy="19" r="2.5" fill="#000"/>
      <circle cx="33" cy="19" r="1.5" fill="#ff4444" opacity="0.8"/>
      <circle cx="33.5" cy="18.5" r="0.6" fill="#fff"/>

      {/* Chest detail */}
      <path d="M26 28 L30 40 L34 28 C32 30 28 30 26 28Z" fill="#009944" opacity="0.6"/>

      {/* Wing feathers detail */}
      <path d="M14 26 C10 23 8 18 12 15" stroke="#00ff88" strokeWidth="0.6" opacity="0.4" fill="none"/>
      <path d="M14 29 C9 26 7 21 10 18" stroke="#00ff88" strokeWidth="0.6" opacity="0.3" fill="none"/>
      <path d="M46 26 C50 23 52 18 48 15" stroke="#00ff88" strokeWidth="0.6" opacity="0.4" fill="none"/>
      <path d="M46 29 C51 26 53 21 50 18" stroke="#00ff88" strokeWidth="0.6" opacity="0.3" fill="none"/>

      {/* Talons */}
      <path d="M26 42 L24 46 M26 42 L26 47 M26 42 L28 46" stroke="#00ff88" strokeWidth="0.8" opacity="0.6"/>
      <path d="M34 42 L32 46 M34 42 L34 47 M34 42 L36 46" stroke="#00ff88" strokeWidth="0.8" opacity="0.6"/>
    </svg>
  );
}

function SysBar({ label, value, color = '#00ff88' }: { label: string; value: number; color?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <span style={{ color: '#3a5a3a', fontSize: '8.5px', width: '26px', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: '4px', background: '#1a2a1a', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{
          width: `${value}%`,
          height: '100%',
          background: color,
          borderRadius: '2px',
          boxShadow: `0 0 4px ${color}55`,
          transition: 'width 0.5s ease',
        }} />
      </div>
      <span style={{ color: '#4a7a4a', fontSize: '8.5px', width: '26px', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
        {Math.round(value)}%
      </span>
    </div>
  );
}

function AgentStatusDot({ status }: { status: string }) {
  const color = status === 'Running' ? '#00ff88' : status === 'Queued' ? '#f0a500' : '#3b82f6';
  const isAnimated = status === 'Running' || status === 'Queued';
  return (
    <div style={{
      width: '7px',
      height: '7px',
      borderRadius: '50%',
      background: color,
      flexShrink: 0,
      boxShadow: isAnimated ? `0 0 6px ${color}` : 'none',
      animation: isAnimated ? (status === 'Running' ? 'pulse-green 1.5s ease-in-out infinite' : 'pulse-amber 1.5s ease-in-out infinite') : 'none',
    }} />
  );
}

export default function LeftPanel({ state, selectedAgent, onSelectAgent }: Props) {
  const tokenPct = Math.min(100, Math.round((state.tokens / state.maxTokens) * 100));
  const tokenLabel = `${(state.tokens / 1000000).toFixed(1)}M / ${(state.maxTokens / 1000000).toFixed(1)}M`;

  const agentTextColor = (s: string) =>
    s === 'Running' ? '#00ff88' : s === 'Queued' ? '#f0a500' : '#3b82f6';

  return (
    <div style={{
      width: '200px',
      minWidth: '200px',
      borderRight: '1px solid #1a2a1a',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflowY: 'auto',
      background: '#090d09',
    }}>

      {/* ── Status card ── */}
      <div style={{ padding: '8px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <EagleLogo />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', paddingTop: '4px' }}>
            <span style={{ color: '#2a4a2a', fontSize: '7.5px', letterSpacing: '0.15em' }}>STATUS</span>
            <div style={{
              color: '#00ff88',
              fontSize: '15px',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textShadow: '0 0 10px rgba(0,255,136,0.5)',
              lineHeight: 1.1,
            }}>
              EXECUTING
            </div>
            <div style={{ marginTop: '4px' }}>
              <span style={{ color: '#2a4a2a', fontSize: '7.5px', letterSpacing: '0.1em' }}>MODE</span>
              <div style={{ color: '#6a8a6a', fontSize: '9px' }}>Autonomous</div>
            </div>
          </div>
        </div>
        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>RISK PROFILE</span>
            <span style={{ color: '#6a8a6a', fontSize: '9px' }}>{state.riskProfile}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>MAX PARALLEL</span>
            <span style={{ color: '#6a8a6a', fontSize: '9px' }}>{state.maxParallel}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>SAFE MODE</span>
            <span style={{ color: '#00ff88', fontSize: '9px', fontWeight: 600 }}>{state.safeMode ? 'ON' : 'OFF'}</span>
          </div>
        </div>
      </div>

      {/* ── Agents ── */}
      <div style={{ flexShrink: 0, borderBottom: '1px solid #1a2a1a' }}>
        <div style={{
          padding: '4px 8px',
          borderBottom: '1px solid #111a11',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{ color: '#3a5a3a', fontSize: '8.5px', letterSpacing: '0.12em' }}>
            AGENTS [{state.agents.filter(a => a.status === 'Running').length}/{state.agents.length}]
          </span>
        </div>

        {state.agents.map(agent => (
          <div
            key={agent.id}
            onClick={() => onSelectAgent(agent.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '5px 8px 5px 10px',
              borderBottom: '1px solid #0c130c',
              cursor: 'pointer',
              background: selectedAgent === agent.id ? '#0d1f0d' : 'transparent',
              borderLeft: selectedAgent === agent.id ? '2px solid #00ff88' : '2px solid transparent',
              transition: 'background 0.15s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: agent.color, fontSize: '10px' }}>⬡</span>
              <span style={{ color: '#9ab89a', fontSize: '9.5px' }}>{agent.name}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AgentStatusDot status={agent.status} />
              <span style={{ color: agentTextColor(agent.status), fontSize: '8.5px' }}>{agent.status}</span>
            </div>
          </div>
        ))}

        {/* Special rows */}
        {[
          { icon: '+', label: 'New Agent', right: 'Launch', rightColor: '#f0a500' },
          { icon: '⚙', label: 'Orchestrator', right: 'Active', rightColor: '#00ff88' },
          { icon: '🧠', label: 'Memory', right: `${state.memoryPercent}%`, rightColor: '#f0a500' },
          { icon: '📚', label: 'Knowledge Base', right: state.knowledgeBase, rightColor: '#3b82f6' },
        ].map((row, i) => (
          <div key={i} style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 8px',
            borderBottom: '1px solid #0c130c',
            cursor: 'pointer',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#3a5a3a', fontSize: '10px' }}>{row.icon}</span>
              <span style={{ color: '#4a6a4a', fontSize: '9px' }}>{row.label}</span>
            </div>
            <span style={{ color: row.rightColor, fontSize: '9px' }}>{row.right}</span>
          </div>
        ))}
      </div>

      {/* ── System Health ── */}
      <div style={{ padding: '8px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        <div style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.15em', marginBottom: '8px' }}>
          SYSTEM HEALTH
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <SysBar label="CPU" value={state.cpu} />
          <SysBar label="MEM" value={state.mem} />
          <SysBar label="NET" value={state.net} />
        </div>
      </div>

      {/* ── Tokens ── */}
      <div style={{ padding: '8px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.12em' }}>TOKENS</span>
          <span style={{ color: '#5a7a5a', fontSize: '8.5px', fontVariantNumeric: 'tabular-nums' }}>{tokenLabel}</span>
        </div>
        {/* Segmented token bar */}
        <div style={{ height: '5px', background: '#1a2a1a', borderRadius: '3px', overflow: 'hidden', display: 'flex' }}>
          <div style={{ width: `${Math.min(tokenPct, 60)}%`, background: '#00ff88', transition: 'width 0.5s' }} />
          <div style={{ width: `${Math.max(0, Math.min(tokenPct - 60, 20))}%`, background: '#f0a500', transition: 'width 0.5s' }} />
          <div style={{ width: `${Math.max(0, tokenPct - 80)}%`, background: '#ff4444', transition: 'width 0.5s' }} />
        </div>
      </div>

      {/* ── Credits & Uptime ── */}
      <div style={{ padding: '8px', flexShrink: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>CREDITS</span>
            <span style={{ color: '#00ff88', fontSize: '12px', fontWeight: 600 }}>
              {state.credits.toLocaleString()}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>UPTIME</span>
            <span style={{ color: '#5a7a5a', fontSize: '9px', fontVariantNumeric: 'tabular-nums' }}>{state.uptime}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
