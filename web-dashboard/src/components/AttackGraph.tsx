import type { GraphNode, GraphEdge } from '../types';

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const TYPE_COLORS: Record<string, string> = {
  host: '#00ff88',
  service: '#3b82f6',
  application: '#a855f7',
  datastore: '#f59e0b',
  external: '#6b7280',
};

const TYPE_ICONS: Record<string, string> = {
  host: '🌐',
  service: '⬡',
  application: '▣',
  datastore: '🗄',
  external: '☁',
};

const LEGEND_ITEMS = [
  { label: 'Host', color: '#00ff88' },
  { label: 'Service', color: '#3b82f6' },
  { label: 'Application', color: '#a855f7' },
  { label: 'Data Store', color: '#f59e0b' },
  { label: 'External', color: '#6b7280' },
];

interface NodeProps {
  node: GraphNode;
  svgW: number;
  svgH: number;
}

function GraphNodeBox({ node, svgW, svgH }: NodeProps) {
  const cx = (node.x / 100) * svgW;
  const cy = (node.y / 100) * svgH;
  const color = TYPE_COLORS[node.type] || '#6b7280';
  const w = 78;
  const h = node.sublabel ? 28 : 20;

  return (
    <g>
      {/* Glow effect for host node */}
      {node.type === 'host' && (
        <rect
          x={cx - w / 2 - 2} y={cy - h / 2 - 2}
          width={w + 4} height={h + 4}
          rx={3} fill="none"
          stroke={color} strokeWidth={0.5}
          opacity={0.3}
        />
      )}
      {/* Main box */}
      <rect
        x={cx - w / 2} y={cy - h / 2}
        width={w} height={h}
        rx={2}
        fill="#0c140c"
        stroke={color}
        strokeWidth={node.type === 'host' ? 1.5 : 1}
        opacity={0.95}
      />
      {/* Icon background */}
      <rect
        x={cx - w / 2} y={cy - h / 2}
        width={16} height={h}
        rx={2}
        fill={color}
        opacity={0.12}
      />
      {/* Icon */}
      <text
        x={cx - w / 2 + 8} y={cy + 4}
        fill={color}
        fontSize={8}
        textAnchor="middle"
        fontFamily="monospace"
      >
        {TYPE_ICONS[node.type] || '?'}
      </text>
      {/* Label */}
      <text
        x={cx - w / 2 + 21} y={node.sublabel ? cy - 3 : cy + 4}
        fill="#c8e6c8"
        fontSize={node.type === 'host' ? 8.5 : 7.5}
        fontFamily="JetBrains Mono, monospace"
        fontWeight={node.type === 'host' ? 700 : 500}
      >
        {node.label}
      </text>
      {node.sublabel && (
        <text
          x={cx - w / 2 + 21} y={cy + 9}
          fill={color}
          fontSize={6.5}
          fontFamily="JetBrains Mono, monospace"
          opacity={0.85}
        >
          {node.sublabel}
        </text>
      )}
    </g>
  );
}

export default function AttackGraph({ nodes, edges }: Props) {
  const svgW = 420;
  const svgH = 290;

  const getCenter = (id: string) => {
    const n = nodes.find(n => n.id === id);
    if (!n) return { x: 0, y: 0 };
    return { x: (n.x / 100) * svgW, y: (n.y / 100) * svgH };
  };

  return (
    <div className="panel flex flex-col h-full overflow-hidden" style={{ background: '#090d09' }}>
      <div className="px-3 py-1 flex-shrink-0" style={{ borderBottom: '1px solid #1a2a1a' }}>
        <span className="panel-title">ATTACK GRAPH</span>
      </div>
      <div className="flex-1 overflow-hidden" style={{ minHeight: 0 }}>
        <svg
          viewBox={`0 0 ${svgW} ${svgH}`}
          width="100%"
          height="100%"
          style={{ display: 'block', background: '#090d09' }}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Grid pattern */}
            <pattern id="smallgrid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#0e1a0e" strokeWidth="0.4"/>
            </pattern>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <rect width="50" height="50" fill="url(#smallgrid)"/>
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#111a11" strokeWidth="0.8"/>
            </pattern>
            {/* Arrow markers */}
            <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L7,3 z" fill="#1e3a1e" />
            </marker>
            <marker id="arrowhead-active" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <path d="M0,0 L0,6 L7,3 z" fill="#2a5a3a" />
            </marker>
          </defs>

          {/* Background */}
          <rect width={svgW} height={svgH} fill="url(#grid)" />

          {/* Edges */}
          {edges.map((edge, i) => {
            const from = getCenter(edge.from);
            const to = getCenter(edge.to);
            const fromNode = nodes.find(n => n.id === edge.from);
            const toNode = nodes.find(n => n.id === edge.to);
            const isActive = fromNode?.type === 'host' || toNode?.type === 'host';

            return (
              <line
                key={i}
                x1={from.x} y1={from.y + 14}
                x2={to.x} y2={to.y - 14}
                stroke={isActive ? '#1e4a2e' : '#162816'}
                strokeWidth={isActive ? 1.2 : 0.8}
                strokeDasharray={isActive ? 'none' : '3,2'}
                markerEnd={`url(#${isActive ? 'arrowhead-active' : 'arrowhead'})`}
                opacity={0.8}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map(node => (
            <GraphNodeBox key={node.id} node={node} svgW={svgW} svgH={svgH} />
          ))}
        </svg>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-3 px-3 py-1 flex-shrink-0" style={{ borderTop: '1px solid #1a2a1a' }}>
        {LEGEND_ITEMS.map(item => (
          <div key={item.label} className="flex items-center gap-1">
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: item.color }} />
            <span style={{ color: '#3a5a3a', fontSize: '7.5px' }}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
