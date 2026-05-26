import { useState } from 'react';

interface Props {
  onCommand: (cmd: string) => void;
}

export default function BottomBar({ onCommand }: Props) {
  const [input, setInput] = useState('');

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim()) {
      onCommand(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex items-center border-t border-zinc-700 bg-zinc-900 shrink-0">
      {/* Left: prompt */}
      <div className="flex-1 flex items-center">
        <span className="text-green-400 font-mono text-xs px-3">argus@cockpit:~$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type command or ask AI..."
          className="flex-1 bg-transparent text-zinc-300 font-mono text-xs outline-none placeholder-zinc-700 py-2"
        />
      </div>
      {/* Right: action buttons */}
      <div className="flex items-center gap-1 px-2 py-1.5 border-l border-zinc-700">
        <Btn label="? Help" />
        <Btn label="Tab Complete" />
        <Btn label="Ctrl+K Commands" />
        <Btn label="Ctrl+D Exit" />
      </div>
    </div>
  );
}

function Btn({ label }: { label: string }) {
  return (
    <button className="text-[13px] font-mono text-zinc-400 hover:text-zinc-200 border border-zinc-700 hover:border-zinc-500 px-1.5 py-0.5 rounded transition-colors">
      {label}
    </button>
  );
}
