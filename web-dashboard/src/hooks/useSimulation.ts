import { useState, useEffect, useCallback, useRef } from 'react';
import type { SystemState, LogLine, ActivityEntry } from '../types';
import { INITIAL_STATE } from '../data/initialState';

let logIdCounter = 100;

// Each scene: a tool run — command first, then its output lines
interface Scene {
  command: string;
  outputs: { text: string; type: LogLine['type'] }[];
}
interface SceneEffect {
  onEnd: (newState: SystemState, p: (s: string) => string, ts: () => string) => void;
}
const ts = () => {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
};
const SCENES: (Scene & SceneEffect)[] = [
  {
    command: '> naabu -host target.domain -p - -rate 3000 -silent',
    outputs: [
      { text: 'target.domain:8080', type: 'output' as const },
      { text: 'target.domain:3306', type: 'output' as const },
    ],
    onEnd: (s, p, t) => {
      s.openPorts = 2;
      s.findings = [...s.findings, { text: p('2 open ports: target.domain:8080, target.domain:3306') }];
      s.activities = [...s.activities, { time: t(), agent: 'Port Scanner', message: p('Port scan: 2 open ports (target.domain:8080, :3306)') }];
    },
  },
  {
    command: '> rustscan -a target.domain --ports 1-65535 --ulimit 5000 -b 1500',
    outputs: [
      { text: 'Open target.domain:22', type: 'success' as const },
      { text: 'Open target.domain:80', type: 'success' as const },
      { text: 'Open target.domain:443', type: 'success' as const },
    ],
    onEnd: (s, p, t) => {
      s.openPorts = 5;
      s.findings = [...s.findings, { text: p('Additional ports: target.domain:22 (SSH), :80 (HTTP), :443 (HTTPS)') }];
      s.activities = [...s.activities, { time: t(), agent: 'Port Scanner', message: p('Additional ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)') }];
    },
  },
  {
    command: '> nmap -sV -sC -p- target.domain --script=banner',
    outputs: [
      { text: '22/tcp   open  ssh     OpenSSH 8.9p1', type: 'output' as const },
      { text: '80/tcp   open  http    nginx 1.22.0', type: 'output' as const },
      { text: '443/tcp  open  https   nginx 1.22.0', type: 'output' as const },
      { text: '8080/tcp open  http    Apache Tomcat 9.0.71', type: 'output' as const },
    ],
    onEnd: (s, p, t) => {
      s.technologies = [
        { name: 'OpenSSH 8.9p1', icon: '🔌', percent: 35 },
        { name: 'Nginx 1.22.0', icon: '🔧', percent: 40 },
        { name: 'Apache Tomcat 9.0.71', icon: '☕', percent: 25 },
      ];
      s.technologies_count = 3;
      s.findings = [...s.findings, { text: 'Service fingerprinting: OpenSSH, Nginx, Apache Tomcat' }];
      s.activities = [...s.activities, { time: t(), agent: 'Tech Analysis', message: 'Service fingerprinting: OpenSSH 8.9p1, Nginx 1.22.0, Tomcat 9.0.71' }];
    },
  },
  {
    command: '> nuclei -target https://target.domain -tags network,ssl,cve',
    outputs: [
      { text: '[nuclei] Loaded 2847 templates, running...', type: 'info' as const },
      { text: '[medium] ssl-certificate-expiry — expires in 14 days', type: 'warn' as const },
      { text: '[info] x-content-type-options header missing', type: 'info' as const },
    ],
    onEnd: (s, p, t) => {
      s.findings = [
        ...s.findings,
        { text: p('SSL cert on target.domain expires in 14 days') },
        { text: 'Missing X-Content-Type-Options header' },
      ];
      s.activities = [...s.activities, { time: t(), agent: 'Vuln Scanner', message: p('2 vulns: SSL expiry + missing X-Content-Type-Options on target.domain') }];
    },
  },
  {
    command: '> ffuf -w /wordlists/web-content.txt -u https://target.domain/FUZZ -mc 200,302,403',
    outputs: [
      { text: '[Status: 200] /login          Size: 4821', type: 'success' as const },
      { text: '[Status: 302] /admin          Size: 0', type: 'success' as const },
      { text: '[Status: 200] /upload         Size: 2103', type: 'success' as const },
      { text: '[Status: 403] /.git           Size: 401', type: 'warn' as const },
      { text: '[Status: 200] /api/v1         Size: 312', type: 'success' as const },
    ],
    onEnd: (s, p, t) => {
      s.findings = [...s.findings, { text: '5 endpoints discovered: /login, /admin, /upload, /.git, /api/v1' }];
      const parentId = s.nodes[0]?.id || 'root';
      for (const ep of ['/login', '/admin', '/upload', '/api/v1']) {
        const nid = `ep_${ep.replace(/[^a-zA-Z0-9]/g, '_')}`;
        if (!s.nodes.find(n => n.id === nid)) {
          s.nodes = [...s.nodes, { id: nid, label: ep, sublabel: 'Web App', x: 18 + s.nodes.length * 21, y: 54, type: 'application', color: '#a855f7' }];
          s.edges = [...s.edges, { from: parentId, to: nid }];
        }
      }
      s.activities = [...s.activities, { time: t(), agent: 'Content Discovery', message: '5 endpoints found: /login, /admin, /upload, /.git, /api/v1' }];
    },
  },
  {
    command: '> whatweb -a 3 https://target.domain',
    outputs: [
      { text: 'PHP[8.1.2], Nginx[1.22.0], jQuery[3.6.0], Bootstrap[5.2]', type: 'output' as const },
      { text: 'Cloudflare, X-XSS-Protection[1;mode=block]', type: 'output' as const },
    ],
    onEnd: (s, p, t) => {
      s.technologies = [
        { name: 'Nginx 1.22.0', icon: '🔧', percent: 25 },
        { name: 'PHP 8.1.2', icon: '🐘', percent: 30 },
        { name: 'Cloudflare', icon: '☁️', percent: 15 },
        { name: 'jQuery 3.6.0', icon: '⚡', percent: 18 },
        { name: 'Bootstrap 5.2', icon: '🎨', percent: 12 },
      ];
      s.technologies_count = 5;
      s.findings = [...s.findings, { text: 'Tech stack: PHP 8.1.2, Nginx, jQuery 3.6.0, Bootstrap 5.2, Cloudflare' }];
      s.activities = [...s.activities, { time: t(), agent: 'Tech Analysis', message: 'Tech stack: PHP 8.1.2, Nginx, jQuery, Bootstrap, Cloudflare' }];
    },
  },
];
;

export function useSimulation() {
  const [state, setState] = useState<SystemState>({ ...INITIAL_STATE });
  const [selectedAgent, setSelectedAgent] = useState('2');
  const wsRef = useRef<WebSocket | null>(null);

  // Replace placeholder domain in all mock data with real target
  function patchDomain(obj: any, realTarget: string): any {
    if (!realTarget || !obj) return obj;
    const placeholder = 'target.domain';
    if (typeof obj === 'string') return obj.replaceAll(placeholder, realTarget);
    if (Array.isArray(obj)) return obj.map(item => patchDomain(item, realTarget));
    if (obj && typeof obj === 'object') {
      const result: any = {};
      for (const [k, v] of Object.entries(obj)) result[k] = patchDomain(v, realTarget);
      return result;
    }
    return obj;
  }

  // Fetch initial target from /api/state and patch mock data immediately
  useEffect(() => {
    fetch('/api/state')
      .then(r => r.json())
      .then(payload => {
        const t = payload.target;
        if (t) {
          setState(prev => ({
            ...patchDomain(prev, t),
            target: t,
          }));
        }
      })
      .catch(() => { /* server not ready yet, WebSocket will handle */ });
  }, []);

  // Keep agents in sync with mode — Subdomain Enum only in non-pentest modes
  useEffect(() => {
    const isBugBounty = state.mode !== 'PENTEST';
    const hasSubdomain = state.agents.some(a => a.id === '1');
    if (isBugBounty && !hasSubdomain) {
      setState(prev => ({
        ...prev,
        agents: [
          { id: '1', name: 'Subdomain Enum', icon: '⬡', status: 'Running', color: '#00ff88' },
          ...prev.agents,
        ],
      }));
    } else if (!isBugBounty && hasSubdomain) {
      setState(prev => ({
        ...prev,
        agents: prev.agents.filter(a => a.id !== '1'),
      }));
    }
  }, [state.mode]);

  // WebSocket connection to backend — replaces mock data with real data
  useEffect(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws`;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let retryCount = 0;

    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        retryCount = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'state') {
            const p = data.payload;
            const realTarget = p.target;
            setState(prev => ({
              ...patchDomain(prev, realTarget),
              target: realTarget || prev.target,
              mode: p.mode || prev.mode,
              sessionId: p.sessionId || prev.sessionId,
              agentStatus: p.agentStatus || prev.agentStatus,
              riskScore: p.riskScore ?? prev.riskScore,
              riskLabel: p.riskLabel || prev.riskLabel,
              targetIP: p.targetIP || prev.targetIP,
              openPorts: p.openPorts ?? prev.openPorts,
              subdomains: p.subdomains ?? prev.subdomains,
              technologies_count: p.technologies_count ?? prev.technologies_count,
              attackSurface: p.attackSurface || prev.attackSurface,
              commandsExecuted: p.commandsExecuted ?? prev.commandsExecuted,
              dataCollected: p.dataCollected || prev.dataCollected,
              findingsCount: p.findingsCount ?? prev.findingsCount,
              vulnerabilities: p.vulnerabilities ?? prev.vulnerabilities,
              activeAgentName: p.activeAgentName || prev.activeAgentName,
              agents: p.agents && p.agents.length ? p.agents : prev.agents,
              pipeline: p.pipeline && p.pipeline.length ? p.pipeline : prev.pipeline,
              findings: p.findings && p.findings.length ? p.findings : prev.findings,
              technologies: p.technologies && p.technologies.length ? p.technologies : prev.technologies,
              discoveries: p.discoveries && p.discoveries.length ? p.discoveries : prev.discoveries,
              nodes: p.nodes && p.nodes.length ? p.nodes : prev.nodes,
              edges: p.edges && p.edges.length ? p.edges : prev.edges,
              logs: p.logs && p.logs.length ? p.logs : prev.logs,
              thinkingLines: p.thinkingLines && p.thinkingLines.length ? p.thinkingLines : prev.thinkingLines,
              activities: p.activities && p.activities.length ? p.activities : prev.activities,
              tokens: p.tokens ?? prev.tokens,
              credits: p.credits ?? prev.credits,
              maxTokens: p.maxTokens ?? prev.maxTokens,
            }));
          }
          if (data.type === 'scan_started') {
            setState(prev => ({ ...prev, agentStatus: 'EXECUTING' }));
          }
          if (data.type === 'scan_completed') {
            setState(prev => ({ ...prev, agentStatus: 'IDLE' }));
          }
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        wsRef.current = null;
        const delay = Math.min(1000 * Math.pow(2, retryCount), 15000);
        retryCount += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) { wsRef.current.onclose = null; wsRef.current.close(); }
    };
  }, []);

  const tick = useCallback(() => {
    elapsedSeconds.current += 1;
    agentTimerRef.current += 1;

    setState(prev => {
      const newState = { ...prev };
      const curTarget = prev.target;
      const p = (s: string) => curTarget ? s.replaceAll('target.domain', curTarget) : s;

      // Time updates
      newState.time = formatTime(elapsedSeconds.current);
      newState.uptime = formatTime(elapsedSeconds.current);
      newState.activeAgentTime = formatShortTime(agentTimerRef.current);

      // Sequential tool scenes — each runs once, never repeats
      if (sceneIdxRef.current < SCENES.length) {
        const scene = SCENES[sceneIdxRef.current];
        // Show command
        const cmdLine: LogLine = { id: ++logIdCounter, text: p(scene.command), type: 'cmd' };
        const outLines: LogLine[] = scene.outputs.map((o, i) => ({ id: ++logIdCounter, text: p(o.text), type: o.type }));
        newState.logs = [...prev.logs.slice(-30), cmdLine, ...outLines];
        commandCountRef.current += 1;
        newState.commandsExecuted = commandCountRef.current;
        scene.onEnd(newState, p, ts);
        sceneIdxRef.current += 1;
      }

      // Sync findings count with actual array
      newState.findingsCount = newState.findings.length;

      return newState;
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [tick]);

  return { state, selectedAgent, setSelectedAgent };
}
