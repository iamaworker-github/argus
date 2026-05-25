import { useState } from 'react';

export default function FooterBar() {
  const [cmd, setCmd] = useState('');

  return (
    <div style={{
      background: '#060a06',
      borderTop: '1px solid #1a2a1a',
      height: '30px',
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      gap: '8px',
      flexShrink: 0,
    }}>
      {/* Prompt prefix */}
      <span style={{ color: '#00ff88', fontSize: '10px', flexShrink: 0, fontFamily: 'JetBrains Mono, monospace' }}>
        strix@cockpit:~#
      </span>

      {/* Cursor + Input */}
      <div style={{ display: 'flex', alignItems: 'center', flex: 1, gap: '4px' }}>
        <span className="cursor-blink" style={{ marginTop: '1px' }} />
        <input
          type="text"
          value={cmd}
          onChange={e => setCmd(e.target.value)}
          placeholder="Type command or ask AI..."
          onKeyDown={e => { if (e.key === 'Enter') setCmd(''); }}
          style={{
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#a8c8a8',
            fontSize: '10px',
            fontFamily: 'JetBrains Mono, monospace',
            flex: 1,
          }}
        />
      </div>

      {/* Keyboard hints */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        <KeyHint hint="?" label="Help" />
        <KeyHint hint="Tab" label="Complete" />
        <KeyHint hint="Ctrl+K" label="Commands" />
        <KeyHint hint="Ctrl+D" label="Exit" />
      </div>
    </div>
  );
}

function KeyHint({ hint, label }: { hint: string; label: string }) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <span style={{
        color: '#00ff88',
        background: '#0d200d',
        border: '1px solid #1a3a1a',
        padding: '0 5px',
        fontSize: '8.5px',
        fontFamily: 'JetBrains Mono, monospace',
        borderRadius: '2px',
      }}>
        {hint}
      </span>
      <span style={{ color: '#3a5a3a', fontSize: '8.5px' }}>{label}</span>
    </span>
  );
}
