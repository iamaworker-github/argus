"""
Attack Graph Visualization — generates interactive D3.js force-directed graph
from graph memory entities and relationships.

Outputs a self-contained HTML file with:
- Force-directed graph layout
- Color-coded nodes by entity type
- Edges labeled with relationship type
- Interactive: click node for details, zoom/pan
- Legend
- Search/filter
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from argus.core.logger import get_logger
from argus.core.graph_memory import GraphMemory, EntityType, get_graph_memory

logger = get_logger()

ENTITY_COLORS = {
    "domain": "#4CAF50", "ip_address": "#2196F3", "url": "#FF9800",
    "email": "#E91E63", "phone": "#9C27B0", "person": "#00BCD4",
    "organization": "#FF5722", "social_account": "#795548",
    "location": "#607D8B", "port": "#3F51B5", "service": "#009688",
    "vulnerability": "#F44336", "cve": "#D32F2F", "technology": "#8BC34A",
    "certificate": "#FFC107", "asn": "#673AB7", "breach": "#B71C1C",
    "exploit": "#FF6F00", "attack_path": "#C2185B",
}

ENTITY_SHAPES = {
    "domain": "circle", "ip_address": "diamond", "email": "triangle",
    "person": "circle", "organization": "rect", "vulnerability": "cross",
    "port": "diamond", "technology": "rect", "cve": "cross",
}

SEVERITY_COLORS = {
    "critical": "#F44336", "high": "#FF5722", "medium": "#FF9800",
    "low": "#FFC107", "info": "#9E9E9E",
}


class AttackGraphVisualizer:
    """Generates interactive D3.js attack graph HTML."""

    def __init__(self, graph: Optional[GraphMemory] = None):
        self._graph = graph or get_graph_memory()

    def generate_html(self, output_path: Optional[str] = None,
                      max_nodes: int = 200,
                      title: str = "Argus Attack Graph") -> str:
        """Generate a self-contained HTML file with D3.js graph."""
        nodes = []
        edges = []

        entities = list(self._graph._entities.values())[:max_nodes]
        for entity in entities:
            color = ENTITY_COLORS.get(entity.type.value, "#999")
            severity = entity.properties.get("severity", "info")
            sev_color = SEVERITY_COLORS.get(severity, "#999")
            nodes.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type.value,
                "group": entity.type.value,
                "color": sev_color if entity.type == EntityType.VULNERABILITY else color,
                "confidence": round(entity.confidence, 2),
                "radius": 5 + (entity.confidence * 5),
                "shape": ENTITY_SHAPES.get(entity.type.value, "circle"),
                "properties": {k: str(v)[:50] for k, v in entity.properties.items()},
            })

        for rel in list(self._graph._relationships.values())[:max_nodes * 2]:
            edges.append({
                "source": rel.source_id,
                "target": rel.target_id,
                "type": rel.type.value,
                "weight": round(rel.weight, 2),
                "confidence": round(rel.confidence, 2),
            })

        data_json = json.dumps({"nodes": nodes, "edges": edges})
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; overflow: hidden; }}
#graph {{ width: 100vw; height: 100vh; }}
.sidebar {{ position: fixed; right: 0; top: 0; width: 320px; height: 100vh; background: rgba(22, 22, 50, 0.95); padding: 20px; overflow-y: auto; border-left: 1px solid #333; transform: translateX(100%); transition: transform 0.3s; }}
.sidebar.open {{ transform: translateX(0); }}
.sidebar h2 {{ color: #4CAF50; margin-bottom: 10px; }}
.sidebar .prop {{ margin: 5px 0; font-size: 13px; }}
.sidebar .prop-key {{ color: #888; }}
.sidebar .prop-val {{ color: #ddd; }}
.legend {{ position: fixed; left: 20px; bottom: 20px; background: rgba(0,0,0,0.8); padding: 15px; border-radius: 8px; font-size: 12px; line-height: 1.8; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; }}
.legend-color {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
.tooltip {{ position: absolute; background: rgba(0,0,0,0.85); color: #fff; padding: 8px 12px; border-radius: 6px; font-size: 13px; pointer-events: none; }}
.stats {{ position: fixed; left: 20px; top: 20px; background: rgba(0,0,0,0.8); padding: 12px 16px; border-radius: 8px; font-size: 13px; }}
.search {{ position: fixed; right: 20px; top: 20px; z-index: 100; }}
.search input {{ padding: 8px 12px; border-radius: 6px; border: 1px solid #444; background: rgba(0,0,0,0.8); color: #fff; width: 250px; font-size: 14px; }}
.node-label {{ font-size: 10px; pointer-events: none; text-shadow: 0 1px 2px #000; }}
.link {{ stroke-opacity: 0.6; }}
</style>
</head>
<body>
<div class="search"><input type="text" id="search" placeholder="Search nodes..." oninput="filterNodes(this.value)"></div>
<div class="stats">Nodes: {len(nodes)} | Edges: {len(edges)} | {timestamp}</div>
<div class="sidebar" id="sidebar"><div id="sidebar-content"></div></div>
<div class="legend" id="legend"></div>
<svg id="graph"></svg>
<script>
const data = {data_json};
const width = window.innerWidth;
const height = window.innerHeight;

const colorMap = {{
    "domain": "#4CAF50", "ip_address": "#2196F3", "url": "#FF9800",
    "email": "#E91E63", "person": "#00BCD4", "organization": "#FF5722",
    "port": "#3F51B5", "vulnerability": "#F44336", "technology": "#8BC34A",
    "cve": "#D32F2F", "certificate": "#FFC107",
}};

// Build legend
const legend = document.getElementById('legend');
const types = [...new Set(data.nodes.map(n => n.type))];
types.forEach(t => {{
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.innerHTML = '<span class="legend-color" style="background:' + (colorMap[t] || '#999') + '"></span>' + t;
    legend.appendChild(div);
}});

const svg = d3.select('#graph');
const g = svg.append('g');
const zoom = d3.zoom().scaleExtent([0.1, 4]).on('zoom', (e) => g.attr('transform', e.transform));
svg.call(zoom);

const simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges).id(d => d.id).distance(d => 100 / (d.weight || 0.5)))
    .force('charge', d3.forceManyBody().strength(-150))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 10));

const link = g.append('g').selectAll('line')
    .data(data.edges).join('line')
    .attr('class', 'link')
    .attr('stroke', '#555')
    .attr('stroke-width', d => Math.max(0.5, d.weight))
    .attr('opacity', d => 0.3 + d.confidence * 0.5);

const node = g.append('g').selectAll('g')
    .data(data.nodes).join('g')
    .attr('class', 'node-group')
    .call(d3.drag()
        .on('start', (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
        .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
        .on('end', (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }})
    );

node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => colorMap[d.type] || '#999')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .on('click', (e, d) => showSidebar(d))
    .on('mouseover', (e, d) => showTooltip(e, d))
    .on('mouseout', hideTooltip);

node.append('text')
    .attr('class', 'node-label')
    .attr('dx', d => d.radius + 4)
    .attr('dy', 3)
    .text(d => d.name.length > 25 ? d.name.substring(0, 22) + '...' : d.name);

const tooltip = d3.select('body').append('div').attr('class', 'tooltip').style('display', 'none');

function showTooltip(e, d) {{
    tooltip.style('display', 'block')
        .style('left', (e.offsetX + 10) + 'px')
        .style('top', (e.offsetY - 10) + 'px')
        .html('<b>' + d.name + '</b><br/>Type: ' + d.type + '<br/>Confidence: ' + d.confidence);
}}

function hideTooltip() {{ tooltip.style('display', 'none'); }}

function showSidebar(d) {{
    const sb = document.getElementById('sidebar');
    const content = document.getElementById('sidebar-content');
    let html = '<h2>' + d.name + '</h2>';
    html += '<p><b>Type:</b> ' + d.type + '</p>';
    html += '<p><b>Confidence:</b> ' + d.confidence + '</p>';
    if (d.properties) {{
        html += '<h3>Properties</h3>';
        for (const [k, v] of Object.entries(d.properties)) {{
            html += '<div class="prop"><span class="prop-key">' + k + ':</span> <span class="prop-val">' + v + '</span></div>';
        }}
    }}
    content.innerHTML = html;
    sb.classList.add('open');
}}

document.addEventListener('click', (e) => {{
    if (!e.target.closest('.node-group') && !e.target.closest('.sidebar')) {{
        document.getElementById('sidebar').classList.remove('open');
    }}
}});

simulation.on('tick', () => {{
    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
}});

function filterNodes(query) {{
    const q = query.toLowerCase();
    node.style('display', d => !q || d.name.toLowerCase().includes(q) || d.type.includes(q) ? null : 'none');
}}
</script>
</body>
</html>"""

        if output_path:
            Path(output_path).write_text(html)
            logger.info(f"Attack graph saved: {output_path}")

        return html
