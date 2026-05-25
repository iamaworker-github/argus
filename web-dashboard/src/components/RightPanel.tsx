import type { SystemState } from '../types';

interface Props {
  state: SystemState;
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div style={{
      color: '#3a5a3a',
      fontSize: '8.5px',
      letterSpacing: '0.15em',
      padding: '5px 10px 4px',
      borderBottom: '1px solid #1a2a1a',
      background: '#0a0f0a',
      flexShrink: 0,
    }}>
      {title}
    </div>
  );
}

function MetaRow({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2px 0' }}>
      <span style={{ color: '#3a5a3a', fontSize: '8.5px', letterSpacing: '0.04em' }}>{label}</span>
      <span style={{ color: valueColor || '#8ab88a', fontSize: '9px', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    </div>
  );
}

export default function RightPanel({ state }: Props) {
  return (
    <div style={{
      width: '190px',
      minWidth: '190px',
      borderLeft: '1px solid #1a2a1a',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      height: '100%',
      background: '#090d09',
    }}>

      {/* ── Target Overview ── */}
      <SectionHeader title="TARGET OVERVIEW" />
      <div style={{ padding: '8px 10px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        <div style={{ marginBottom: '6px' }}>
          <div style={{ color: '#3a5a3a', fontSize: '7.5px', letterSpacing: '0.1em', marginBottom: '2px' }}>Primary Target</div>
          <div style={{ color: '#00ff88', fontSize: '12px', fontWeight: 700, textShadow: '0 0 8px rgba(0,255,136,0.3)' }}>
            {state.target}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <MetaRow label="IP Address" value={state.targetIP} />
          <MetaRow label="Open Ports" value={String(state.openPorts)} />
          <MetaRow label="Subdomains" value={String(state.subdomains)} />
          <MetaRow label="Technologies" value={String(state.technologies_count)} />
          <MetaRow label="Attack Surface" value={state.attackSurface} valueColor="#f0a500" />
        </div>
      </div>

      {/* ── Top Technologies ── */}
      <SectionHeader title="TOP TECHNOLOGIES" />
      <div style={{ padding: '6px 10px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        {state.technologies.map((tech, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '3px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ fontSize: '9px' }}>{tech.icon}</span>
              <span style={{ color: '#8ab88a', fontSize: '9px' }}>{tech.name}</span>
            </div>
            <span style={{ color: '#3a5a3a', fontSize: '8.5px' }}>{tech.percent}%</span>
          </div>
        ))}
      </div>

      {/* ── Recent Discoveries ── */}
      <SectionHeader title="RECENT DISCOVERIES" />
      <div style={{ padding: '6px 10px', borderBottom: '1px solid #1a2a1a', flexShrink: 0 }}>
        {state.discoveries.slice(-5).map((d, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2.5px 0' }}>
            <span style={{ color: '#6a9a6a', fontSize: '9px' }}>{d.name}</span>
            <span style={{ color: '#2a4a2a', fontSize: '8px', fontVariantNumeric: 'tabular-nums' }}>{d.time}</span>
          </div>
        ))}
      </div>

      {/* ── Session Metrics ── */}
      <SectionHeader title="SESSION METRICS" />
      <div style={{ padding: '6px 10px', flexShrink: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <MetaRow label="Commands Executed" value={String(state.commandsExecuted)} />
          <MetaRow label="Data Collected" value={state.dataCollected} />
          <MetaRow label="Findings" value={String(state.findingsCount)} />
          <MetaRow label="Vulnerabilities" value={String(state.vulnerabilities)} />
          <MetaRow label="Time Elapsed" value={state.time} />
        </div>
      </div>
    </div>
  );
}
