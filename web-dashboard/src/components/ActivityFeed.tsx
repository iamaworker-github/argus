import type { ActivityEntry } from '../types';

interface Props {
  activities: ActivityEntry[];
  verbosity: string;
}

export default function ActivityFeed({ activities, verbosity }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '5px 10px',
        borderBottom: '1px solid #1a2a1a',
        background: '#0a0f0a',
      }}>
        <span style={{ color: '#3a5a3a', fontSize: '8.5px', letterSpacing: '0.15em' }}>ACTIVITY FEED</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ color: '#2a4a2a', fontSize: '8px', letterSpacing: '0.1em' }}>VERBOSITY</span>
          <div style={{
            background: '#0d200d',
            border: '1px solid #2a4a2a',
            color: '#00ff88',
            fontSize: '9px',
            padding: '1px 8px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            cursor: 'pointer',
          }}>
            {verbosity}
            <span style={{ color: '#3a5a3a', fontSize: '8px' }}>▾</span>
          </div>
        </div>
      </div>
      {/* Rows */}
      <div style={{ maxHeight: '95px', overflowY: 'auto' }}>
        {activities.slice(-5).map((entry, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '3px 10px',
              borderBottom: '1px solid #0d160d',
            }}
          >
            <span style={{ color: '#3a5a3a', fontSize: '8.5px', fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
              {entry.time}
            </span>
            <span style={{ color: '#5a8a5a', fontSize: '9px', flexShrink: 0, minWidth: '100px' }}>
              {entry.agent}
            </span>
            <span style={{ color: '#8ab88a', fontSize: '9px' }}>{entry.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
