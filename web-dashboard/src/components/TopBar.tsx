interface Props {
  elapsed: string;
  sessionId: string;
  target: string;
}

export default function TopBar({ elapsed, sessionId, target }: Props) {
  return (
    <div className="flex items-center justify-between px-3 py-1 border-b border-zinc-700 bg-zinc-950 shrink-0">
      <div className="flex items-center gap-3">
        <span className="text-yellow-400 font-bold font-mono text-sm tracking-widest">ARGUS</span>
        <span className="text-zinc-600 font-mono text-xs">v0.0.1</span>
        <span className="text-zinc-600 font-mono text-xs">|</span>
        <span className="text-zinc-400 font-mono text-xs tracking-widest">AUTONOMOUS AI CYBERSECURITY AGENT</span>
      </div>
      <div className="flex items-center gap-4 font-mono text-xs">
        <span className="text-zinc-500">OPERATION: <span className="text-yellow-400 font-bold">PENTEST</span></span>
        <span className="text-zinc-500">TARGET: <span className="text-green-400">{target}</span></span>
        <span className="text-zinc-500">SESSION: <span className="text-cyan-400">{sessionId}</span></span>
        <span className="text-zinc-500">TIME: <span className="text-white">{elapsed}</span></span>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 font-bold">LIVE</span>
        </div>
      </div>
    </div>
  );
}
