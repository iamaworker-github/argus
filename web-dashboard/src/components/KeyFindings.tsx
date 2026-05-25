import type { Finding } from '../types';

interface Props {
  findings: Finding[];
  riskScore: number;
  riskLabel: string;
}

const RISK_COLORS: Record<string, string> = {
  Low: '#00ff88',
  Medium: '#f0a500',
  High: '#ff6b35',
  Critical: '#ff4444',
};

export default function KeyFindings({ findings, riskScore, riskLabel }: Props) {
  const riskColor = RISK_COLORS[riskLabel] || '#f0a500';
  const totalSegs = 10;
  const filledSegs = Math.round((riskScore / 10) * totalSegs);

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '5px 10px',
        borderBottom: '1px solid #1a2a1a',
        background: '#0a0f0a',
      }}>
        <span style={{ color: '#3a5a3a', fontSize: '8.5px', letterSpacing: '0.15em' }}>KEY FINDINGS</span>
      </div>

      <div style={{ display: 'flex', gap: '0', padding: '8px 10px' }}>
        {/* Findings list */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {findings.map((f, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#00ff88', fontSize: '10px', flexShrink: 0 }}>✓</span>
              <span style={{ color: '#7ab07a', fontSize: '9.5px' }}>{f.text}</span>
            </div>
          ))}
        </div>

        {/* Risk Score */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          paddingLeft: '12px',
          borderLeft: '1px solid #1a2a1a',
          minWidth: '90px',
          gap: '3px',
        }}>
          <span style={{ color: '#3a5a3a', fontSize: '7.5px', letterSpacing: '0.12em' }}>RISK SCORE</span>
          <div style={{
            color: riskColor,
            fontSize: '34px',
            fontWeight: 700,
            lineHeight: 1,
            textShadow: `0 0 16px ${riskColor}55`,
          }}>
            {riskScore.toFixed(1)}
          </div>
          <span style={{ color: riskColor, fontSize: '10px', fontWeight: 600, letterSpacing: '0.05em' }}>
            {riskLabel}
          </span>
          {/* Segmented bar */}
          <div style={{ display: 'flex', gap: '2px', marginTop: '4px' }}>
            {Array.from({ length: totalSegs }).map((_, idx) => (
              <div
                key={idx}
                style={{
                  width: '7px',
                  height: '4px',
                  background: idx < filledSegs ? riskColor : '#1a2a1a',
                  borderRadius: '1px',
                  opacity: idx < filledSegs ? 0.5 + (idx / totalSegs) * 0.5 : 1,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
