"""
Autonomous AI-driven security testing agent
"""

import json
from typing import Any, Dict, List, Optional

import httpx

from argus.agents.base_agent import AgentResult, BaseAgent, Finding
from argus.agents.llm_client import LLMClient
from argus.core.logger import get_logger

logger = get_logger()


class AutonomousSecurityAgent(BaseAgent):
    """Autonomous security agent using plan -> execute -> evaluate loop."""

    def __init__(
        self,
        target: str,
        event_bus=None,
        memory_manager=None,
        max_iterations: int = 5,
        scope: Optional[List[str]] = None,
        instruction: Optional[str] = None,
    ):
        super().__init__(
            "Autonomous Security Agent",
            target,
            event_bus=event_bus,
            memory_manager=memory_manager,
            scope=scope,
        )
        self.max_iterations = max(1, max_iterations)
        self.instruction = instruction.strip() if instruction else None
        self.llm_client = LLMClient()
        self.observations: List[Dict[str, Any]] = []

    async def execute(self) -> AgentResult:
        logger.info(f"{self.name}: Autonomous scan started on {self.target}")

        if not self.llm_client.config.has_ai_enabled:
            self.add_finding(Finding(
                title="Autonomous mode unavailable",
                description="AI API keys are not configured; autonomous reasoning cannot run.",
                severity="info",
                category="configuration",
                evidence="No OpenAI/Anthropic API key detected in configuration",
                remediation="Configure OPENAI_API_KEY or ANTHROPIC_API_KEY for autonomous mode",
                confidence=1.0,
                validation_status="unvalidated_poc_missing",
            ))
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                findings=self.findings,
                execution_time=0,
                metadata={"autonomous_enabled": False},
            )

        for iteration in range(1, self.max_iterations + 1):
            try:
                plan = await self._generate_plan(iteration)
                if not plan:
                    logger.debug(f"{self.name}: No actionable plan at iteration {iteration}")
                    continue

                for action in plan:
                    observation = await self._execute_action(action)
                    self.observations.append(observation)
                    await self._evaluate_observation(action, observation)

            except Exception as exc:
                logger.debug(f"{self.name}: Iteration {iteration} failed: {exc}")

        return AgentResult(
            agent_name=self.name,
            status=self.status,
            findings=self.findings,
            execution_time=0,
            metadata={
                "autonomous_enabled": True,
                "max_iterations": self.max_iterations,
                "observations": len(self.observations),
            },
        )

    async def _generate_plan(self, iteration: int) -> List[Dict[str, Any]]:
        system = (
            "You are an autonomous web security planner. "
            "Return ONLY valid JSON array of actions. "
            "Each action must include: method, path, params, data, hypothesis."
        )
        instruction_context = (
            f"Focused instruction: {self.instruction}\n"
            "Treat this instruction as high-priority guidance while respecting target/scope constraints.\n"
            if self.instruction
            else ""
        )
        prompt = (
            f"Target: {self.target}\n"
            f"Scope paths: {self.scope or []}\n"
            f"Iteration: {iteration}/{self.max_iterations}\n"
            f"Recent observations (up to 5): {self.observations[-5:]}\n"
            f"{instruction_context}\n"
            "Generate up to 3 high-signal security test actions focused on exploitable behavior. "
            "Prefer scoped paths when provided. "
            "Output format example:\n"
            "[{\"method\":\"GET\",\"path\":\"/login\",\"params\":{\"q\":\"' OR '1'='1\"},"
            "\"data\":{},\"hypothesis\":\"Possible SQLi in search parameter\"}]"
        )

        response = await self.llm_client.generate(prompt=prompt, system=system, max_tokens=700)
        parsed = self._extract_json(response.content)
        if isinstance(parsed, list):
            return [a for a in parsed if isinstance(a, dict)]
        return []

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        method = str(action.get("method", "GET")).upper()
        path = str(action.get("path", "/"))
        params = action.get("params") or {}
        data = action.get("data") or {}

        url = self._build_url(path)

        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            if method == "POST":
                response = await client.post(url, params=params, data=data)
            else:
                response = await client.get(url, params=params)

        body_preview = response.text[:800]
        return {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "response_length": len(response.text),
            "body_preview": body_preview,
            "hypothesis": action.get("hypothesis", ""),
            "params": params,
            "data": data,
        }

    async def _evaluate_observation(self, action: Dict[str, Any], observation: Dict[str, Any]) -> None:
        system = (
            "You are a security verifier. Decide if the observation indicates a real vulnerability. "
            "Return ONLY JSON object with keys: vulnerable (bool), title, severity, category, "
            "description, evidence, proof_of_concept, remediation, confidence."
        )
        prompt = (
            f"Target: {self.target}\n"
            f"Action: {action}\n"
            f"Observation: {observation}\n\n"
            "Be conservative. Mark vulnerable=true only if there is meaningful exploit evidence."
        )

        response = await self.llm_client.generate(prompt=prompt, system=system, max_tokens=900)
        parsed = self._extract_json(response.content)
        if not isinstance(parsed, dict) or not parsed.get("vulnerable"):
            return

        finding = Finding(
            title=str(parsed.get("title", "Autonomous vulnerability signal")),
            description=str(parsed.get("description", action.get("hypothesis", "Potential vulnerability detected"))),
            severity=str(parsed.get("severity", "medium")).lower(),
            category=str(parsed.get("category", "autonomous")),
            evidence=str(parsed.get("evidence", observation.get("body_preview", "")[:300])),
            proof_of_concept=parsed.get("proof_of_concept"),
            remediation=parsed.get("remediation"),
            confidence=float(parsed.get("confidence", 0.7)),
            reproducibility_steps=[
                f"Request URL: {observation.get('url')}",
                f"Method: {observation.get('method')}",
                f"Parameters: {observation.get('params')}",
                f"Data: {observation.get('data')}",
            ],
            fix_hint=parsed.get("remediation"),
        )
        self.add_finding(finding)

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path

        base = self.target.rstrip("/")
        if not (base.startswith("http://") or base.startswith("https://")):
            base = f"http://{base}"

        norm_path = path if path.startswith("/") else f"/{path}"
        return f"{base}{norm_path}"

    def _extract_json(self, content: str) -> Any:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            return json.loads(text)
        except Exception:
            start_obj = text.find("{")
            end_obj = text.rfind("}")
            if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
                try:
                    return json.loads(text[start_obj:end_obj + 1])
                except Exception:
                    pass

            start_arr = text.find("[")
            end_arr = text.rfind("]")
            if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
                try:
                    return json.loads(text[start_arr:end_arr + 1])
                except Exception:
                    pass
        return None
