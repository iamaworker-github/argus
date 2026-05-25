import type { PipelineStage } from '../types';

interface Props {
  stages: PipelineStage[];
}

export default function OperationPipeline({ stages }: Props) {
  return (
    <div className="panel px-3 py-2 flex-shrink-0" style={{ borderBottom: '1px solid #1a2a1a', minHeight: '72px' }}>
      <div className="panel-title mb-2">OPERATION PIPELINE</div>
      <div className="flex items-start justify-between relative" style={{ paddingTop: '6px' }}>
        {/* Connector lines behind everything */}
        <div style={{ position: 'absolute', top: '11px', left: '8%', right: '8%', height: '1px', background: '#1a2a1a', zIndex: 0 }} />

        {stages.map((stage, i) => {
          const isComplete = stage.completed === stage.total && stage.total > 0;
          const isActive = stage.active;
          const pct = stage.total > 0 ? (stage.completed / stage.total) * 100 : 0;

          const dotColor = isComplete ? '#00ff88' : isActive ? '#f0a500' : '#2a3a2a';
          const textColor = isComplete ? '#6ab88a' : isActive ? '#f0a500' : '#3a5a3a';
          const countColor = isComplete ? '#00cc55' : isActive ? '#f0a500' : '#2a4a2a';
          const lineColor = isComplete ? '#004422' : '#1a2a1a';

          return (
            <div key={stage.name} className="flex flex-col items-center gap-1 relative" style={{ flex: 1, zIndex: 1 }}>
              {/* Segment line */}
              {i < stages.length - 1 && (
                <div style={{
                  position: 'absolute',
                  left: '50%',
                  top: '4px',
                  width: '100%',
                  height: '2px',
                  background: lineColor,
                  zIndex: 0,
                }} />
              )}
              {/* Dot */}
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: isActive ? 'transparent' : dotColor,
                border: `2px solid ${dotColor}`,
                boxShadow: isActive ? `0 0 10px ${dotColor}, 0 0 4px ${dotColor}` : isComplete ? `0 0 6px #00aa44` : 'none',
                zIndex: 2,
                flexShrink: 0,
              }} />
              {/* Stage name */}
              <span style={{ color: textColor, fontSize: '8.5px', letterSpacing: '0.03em', textAlign: 'center', lineHeight: 1.2, marginTop: '2px' }}>
                {stage.name}
              </span>
              {/* Progress count */}
              {stage.total > 0 && (
                <span style={{ color: countColor, fontSize: '8px', fontVariantNumeric: 'tabular-nums' }}>
                  {stage.completed}/{stage.total}
                </span>
              )}
              {/* Active stage progress bar */}
              {isActive && stage.total > 0 && (
                <div style={{ width: '36px', height: '2px', background: '#1a2a1a', borderRadius: '1px', marginTop: '1px' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: '#f0a500', borderRadius: '1px', transition: 'width 0.5s' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
