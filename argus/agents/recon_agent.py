"""
Reconnaissance agent for information gathering
"""


import asyncio
from typing import List, Dict, Any
import httpx
import dns.resolver
from argus.agents.base_agent import BaseAgent, AgentResult, Finding, AgentStatus
from argus.core.logger import get_logger

logger = get_logger()


class ReconAgent(BaseAgent):
    """Agent for reconnaissance and information gathering"""

    def __init__(self, target: str, event_bus=None, memory_manager=None, mode: str = "pentest", scope=None):
        super().__init__("Recon Agent", target, event_bus=event_bus, memory_manager=memory_manager, scope=scope)
        self.discovered_subdomains: List[str] = []
        self.discovered_endpoints: List[str] = []
        self.technologies: List[str] = []
        self.mode = mode  # Store mode for blackbox testing

    async def _emit_thought(self, thought: str, thought_type: str = "reasoning", phase: str = "") -> None:
        if self.event_bus:
            try:
                from argus.core.events import AgentThinkingEvent
                await self.event_bus.publish_event(AgentThinkingEvent(
                    agent_name=self.name,
                    thought=thought,
                    thought_type=thought_type,
                    phase=phase or "",
                ))
            except Exception:
                pass

    async def execute(self) -> AgentResult:
        """Execute reconnaissance"""
        logger.info(f"{self.name}: Gathering intelligence on {self.target}")
        await self._emit_thought(f"Starting reconnaissance on {self.target}...", "analyzing", "recon")

        # Skip subdomain enumeration in pentest mode (blackbox only)
        if self.mode != "pentest":
            # DNS enumeration (only for OSINT/BugBounty modes)
            await self._dns_enumeration()

        # Blackbox testing (always run)
        # Technology detection
        await self._detect_technologies()

        # Endpoint discovery
        await self._discover_endpoints()

        return AgentResult(
            agent_name=self.name,
            status=self.status,
            findings=self.findings,
            execution_time=0,
            metadata={
                "subdomains": self.discovered_subdomains,
                "endpoints": self.discovered_endpoints,
                "technologies": self.technologies,
            }
        )

    async def _dns_enumeration(self) -> None:
        """Perform DNS enumeration"""
        await self._emit_thought("Enumerating DNS records and subdomains...", "recon", "dns")
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            # Common subdomains to check
            common_subdomains = [
                "www", "mail", "ftp", "admin", "api", "dev", "staging",
                "test", "portal", "app", "dashboard", "blog", "shop"
            ]

            for subdomain in common_subdomains:
                try:
                    full_domain = f"{subdomain}.{self.target}"
                    answers = resolver.resolve(full_domain, 'A')
                    if answers:
                        self.discovered_subdomains.append(full_domain)
                        logger.debug(f"Found subdomain: {full_domain}")
                except:
                    pass

            if self.discovered_subdomains:
                self.add_finding(Finding(
                    title="Subdomains discovered",
                    description=f"Found {len(self.discovered_subdomains)} subdomains",
                    severity="info",
                    category="recon",
                    evidence=f"Subdomains: {', '.join(self.discovered_subdomains[:5])}...",
                    confidence=1.0,
                ))

        except Exception as e:
            logger.debug(f"DNS enumeration error: {e}")

    async def _detect_technologies(self) -> None:
        """Detect web technologies using httpx -td"""
        import json as _json
        await self._emit_thought(f"Detecting web technologies on {self.target} with httpx -td...", "recon", "tech_detection")
        try:
            domain = self.target.split('/')[0].split(':')[0]
            httpx_cmd = ["pd-httpx", "-u", domain, "-td", "-json", "-sc", "-silent"]
            httpx_cmd.extend(self.format_auth_args())
            proc = await asyncio.create_subprocess_exec(
                *httpx_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=20)
            for line in stdout.decode().strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = _json.loads(line)
                    techs = data.get("tech", []) or []
                    if techs:
                        self.technologies.extend(techs)
                except Exception:
                    pass

            if self.technologies:
                self.add_finding(Finding(
                    title="Technologies detected",
                    description=f"Identified {len(self.technologies)} technologies via httpx -td",
                    severity="info",
                    category="recon",
                    evidence=f"Technologies: {', '.join(set(self.technologies))}",
                    confidence=0.9,
                ))
        except Exception as e:
            logger.debug(f"httpx -td technology detection error: {e}")

    async def _discover_endpoints(self) -> None:
        """Discover endpoints using default wordlist"""
        from pathlib import Path

        # Load default wordlist
        wordlist_path = Path(__file__).parent.parent / "data" / "wordlists" / "default_pentest_wordlist.txt"

        paths_to_test = []

        if self.scope:
            paths_to_test = [p if p.startswith("/") else f"/{p}" for p in self.scope]
            logger.info(f"Diff mode active: testing {len(paths_to_test)} scoped paths")
        elif wordlist_path.exists():
            # Load wordlist (limit to first 1000 for quick scan)
            try:
                with open(wordlist_path, 'r') as f:
                    paths_to_test = [f"/{line.strip()}" for line in f.readlines()[:1000] if line.strip()]
                logger.info(f"Loaded {len(paths_to_test)} paths from default wordlist")
            except Exception as e:
                logger.warning(f"Failed to load wordlist: {e}, using fallback")
                paths_to_test = self._get_fallback_paths()
        else:
            logger.warning(f"Wordlist not found at {wordlist_path}, using fallback")
            paths_to_test = self._get_fallback_paths()

        # Sensitive paths to flag
        sensitive_paths = ["/.git", "/.env", "/backup", "/.git/config", "/config.php",
                          "/wp-config.php", "/.aws", "/.ssh", "/id_rsa"]

        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False, headers=self.get_http_client_headers()) as client:
            for path in paths_to_test:
                try:
                    url = f"http://{self.target}{path}"
                    response = await client.get(url)

                    if response.status_code in [200, 301, 302, 401, 403]:
                        self.discovered_endpoints.append(path)
                        logger.debug(f"Found endpoint: {path} ({response.status_code})")

                        # Flag sensitive endpoints
                        if any(sensitive in path for sensitive in sensitive_paths):
                            self.add_finding(Finding(
                                title=f"Sensitive endpoint exposed: {path}",
                                description=f"Potentially sensitive endpoint is accessible",
                                severity="medium",
                                category="recon",
                                evidence=f"HTTP {response.status_code} at {url}",
                                confidence=0.9,
                            ))

                except Exception as e:
                    pass  # Ignore connection errors

            if self.discovered_endpoints:
                self.add_finding(Finding(
                    title="Endpoints discovered",
                    description=f"Found {len(self.discovered_endpoints)} accessible endpoints",
                    severity="info",
                    category="recon",
                    evidence=f"Endpoints: {', '.join(self.discovered_endpoints[:10])}...",
                    confidence=1.0,
                ))

    def _get_fallback_paths(self) -> list:
        """Fallback paths if wordlist not available"""
        return [
            "/admin", "/login", "/api", "/api/v1", "/dashboard",
            "/wp-admin", "/phpmyadmin", "/.git", "/.env",
            "/config", "/backup", "/test", "/debug", "/robots.txt",
            "/sitemap.xml", "/swagger", "/graphql", "/api/docs"
        ]
