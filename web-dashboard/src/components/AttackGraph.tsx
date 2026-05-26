import { useState } from 'react';
import type { GraphNode, GraphEdge } from '../types';

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const nodeColors: Record<string, { fill: string; stroke: string; text: string }> = {
  Host: { fill: '#1e3a2f', stroke: '#4ade80', text: '#4ade80' },
  Service: { fill: '#1e2a3a', stroke: '#60a5fa', text: '#60a5fa' },
  Application: { fill: '#2a1e3a', stroke: '#c084fc', text: '#c084fc' },
  DataStore: { fill: '#3a2a1e', stroke: '#fb923c', text: '#fb923c' },
  External: { fill: '#3a1e1e', stroke: '#f87171', text: '#f87171' },
};

const stateOpacity: Record<string, number> = {
  discovered: 1,
  pending: 0.45,
  compromised: 1,
  safe: 0.7,
};

const typeLegend = [
  { label: 'Host', color: '#4ade80' },
  { label: 'Service', color: '#60a5fa' },
  { label: 'Application', color: '#c084fc' },
  { label: 'DataStore', color: '#fb923c' },
  { label: 'External', color: '#f87171' },
];

export default function AttackGraph({ nodes, edges }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const W = 100;
  const H = 100;

  const getNode = (id: string) => nodes.find((n) => n.id === id);

  return (
    <div className={`flex flex-col ${isCollapsed ? '' : 'h-40'}`}>
      <div
        className="flex items-center justify-between px-3 py-1.5 border-b border-zinc-700 shrink-0 cursor-pointer hover:bg-zinc-900"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="text-zinc-400 font-mono text-[12px] font-bold uppercase tracking-widest">Attack Graph</span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span className="text-green-400 font-mono text-[13px]">LIVE</span>
          </div>
          <span className="text-zinc-500 text-[12px] font-mono">{isCollapsed ? '▶' : '▼'}</span>
        </div>
      </div>

      {!isCollapsed && (
      <div className="flex-1 relative overflow-hidden bg-zinc-950 p-1 min-h-0">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#27272a" strokeWidth="0.2" />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />

          {/* Edges */}
          {edges.map((edge, i) => {
            const from = getNode(edge.from);
            const to = getNode(edge.to);
            if (!from || !to) return null;
            return (
              <line
                key={i}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke="#3f3f46"
                strokeWidth="0.5"
                strokeDasharray={to.state === 'pending' ? '2 1' : undefined}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const cfg = nodeColors[node.type];
            const opacity = stateOpacity[node.state];
            const isPending = node.state === 'pending';
            return (
              <g key={node.id} opacity={opacity}>
                {/* Glow for discovered */}
                {node.state === 'discovered' && (
                  <circle cx={node.x} cy={node.y} r="5" fill={cfg.stroke} opacity="0.15" />
                )}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="3.5"
                  fill={cfg.fill}
                  stroke={cfg.stroke}
                  strokeWidth={isPending ? '0.4' : '0.8'}
                  strokeDasharray={isPending ? '1.5 0.8' : undefined}
                />
                {/* Node type icon */}
                <text
                  x={node.x}
                  y={node.y + 0.8}
                  textAnchor="middle"
                  fontSize="3"
                  fill={cfg.text}
                >
                  {node.type === 'Host' ? '⬡' : node.type === 'Service' ? '◈' : node.type === 'Application' ? '◉' : node.type === 'DataStore' ? '▣' : '◆'}
                </text>
                {/* Label */}
                <text
                  x={node.x}
                  y={node.y + 7}
                  textAnchor="middle"
                  fontSize="2.2"
                  fill={isPending ? '#52525b' : cfg.text}
                >
                  {node.label.length > 25 ? node.label.slice(0, 24) + '…' : node.label}
                </text>
                {/* Pending badge */}
                {isPending && (
                  <text x={node.x} y={node.y - 5} textAnchor="middle" fontSize="1.8" fill="#6b7280">
                    pending
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="flex flex-wrap gap-x-2 gap-y-0.5 px-2 py-1 border-t border-zinc-800 bg-zinc-950">
          {typeLegend.map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: l.color }} />
              <span className="text-[12px] font-mono" style={{ color: l.color }}>{l.label}</span>
            </div>
          ))}
          <div className="flex items-center gap-1 ml-2">
            <div className="w-3 h-px border-t border-dashed border-zinc-600" />
            <span className="text-[12px] font-mono text-zinc-600">pending</span>
          </div>
        </div>
      </div>
      )}
    </div>
  );
}
