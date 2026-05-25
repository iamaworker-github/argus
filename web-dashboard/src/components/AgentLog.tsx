import { useEffect, useRef } from 'react';
import type { LogLine } from '../types';

interface Props {
  agentName: string;
  agentTime: string;
  logs: LogLine[];
  thinkingLines: string[];
  tokensUsed: string;
}

export default function AgentLog({ agentName, agentTime, logs, thinkingLines, tokensUsed }: Props) {
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* ── Agent Header ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '5px 10px',
        borderBottom: '1px solid #1a2a1a',
        background: '#0a0f0a',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#3b82f6', fontSize: '12px' }}>⬡</span>
          <span style={{ color: '#a8c8a8', fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em' }}>
            {agentName}
          </span>
          <div className="dot-running" />
          <span style={{ color: '#00ff88', fontSize: '9px', letterSpacing: '0.08em' }}>RUNNING</span>
        </div>
        <span style={{ color: '#3a5a3a', fontSize: '9px', fontVariantNumeric: 'tabular-nums' }}>
          {agentTime}
        </span>
      </div>

      {/* ── Log Output ── */}
      <div
        ref={logRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 10px',
          minHeight: 0,
        }}
      >
        {logs.map((line) => {
          const color =
            line.type === 'cmd' ? '#b8d8b8' :
            line.type === 'success' ? '#00ff88' :
            line.type === 'info' ? '#5a9a7a' :
            line.type === 'warn' ? '#f0a500' :
            '#4a6a4a';

          return (
            <div
              key={line.id}
              style={{
                color,
                fontSize: '10px',
                lineHeight: '1.55',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                fontFamily: 'JetBrains Mono, monospace',
              }}
            >
              {line.text || '\u00A0'}
            </div>
          );
        })}
      </div>

      {/* ── Thinking Panel ── */}
      <div style={{
        flexShrink: 0,
        margin: '0 6px 6px 6px',
        padding: '8px 10px',
        background: '#070c07',
        border: '1px solid #1e3a1e',
        borderLeft: '2px solid #2a6a4a',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '5px' }}>
          <span style={{ color: '#f0a500', fontSize: '9px', fontWeight: 600, letterSpacing: '0.12em' }}>
            THINKING — {agentName}
          </span>
        </div>
        {thinkingLines.map((line, i) => (
          <div
            key={i}
            style={{
              color: '#5a8a6a',
              fontSize: '9.5px',
              lineHeight: '1.65',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            {line}
          </div>
        ))}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '4px' }}>
          <span style={{ color: '#2a4a2a', fontSize: '8.5px', letterSpacing: '0.05em' }}>
            TOKENS: {tokensUsed}
          </span>
        </div>
      </div>
    </div>
  );
}
