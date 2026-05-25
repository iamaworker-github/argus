import type { SystemState } from '../types';

interface Props {
  state: SystemState;
}

export default function HeaderBar({ state }: Props) {
  return (
    <div className="header-bar flex items-center justify-between px-3 flex-shrink-0">
      {/* Left: Brand */}
      <div className="flex items-center gap-3">
        <span className="strix-logo">STRIX</span>
        <span className="version-tag">v0.8.3</span>
        <span style={{ color: '#3a5a3a', fontSize: '9px', letterSpacing: '0.18em' }}>
          AUTONOMOUS AI CYBERSECURITY COCKPIT
        </span>
      </div>

      {/* Right: Status */}
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2">
          <span style={{ color: '#3a5a3a', fontSize: '9px', letterSpacing: '0.12em' }}>OPERATION:</span>
          <span style={{ color: '#f0a500', fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em' }}>{state.mode}</span>
        </div>
        <div className="flex items-center gap-2">
          <span style={{ color: '#3a5a3a', fontSize: '9px', letterSpacing: '0.12em' }}>TARGET:</span>
          <span style={{ color: '#00ff88', fontSize: '10px', letterSpacing: '0.05em' }}>{state.target}</span>
        </div>
        <div className="flex items-center gap-2">
          <span style={{ color: '#3a5a3a', fontSize: '9px', letterSpacing: '0.12em' }}>SESSION:</span>
          <span style={{ color: '#c8e6c8', fontSize: '10px' }}>{state.sessionId}</span>
        </div>
        <div className="flex items-center gap-2">
          <span style={{ color: '#3a5a3a', fontSize: '9px', letterSpacing: '0.12em' }}>TIME:</span>
          <span style={{ color: '#c8e6c8', fontSize: '10px', fontVariantNumeric: 'tabular-nums' }}>{state.time}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="dot-live" />
          <span style={{ color: '#00ff88', fontSize: '9px', letterSpacing: '0.1em', fontWeight: 600 }}>LIVE</span>
        </div>
      </div>
    </div>
  );
}
