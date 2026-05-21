"""
ArgusAlerter — Multi-platform alert system for critical findings.
Sends notifications to Telegram, Discord, or Slack.
Hermes-inspired send_message capability.
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from argus.core.logger import get_logger

logger = get_logger()


@dataclass
class AlertConfig:
    telegram_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook: str = ""
    slack_webhook: str = ""
    enabled: bool = True
    min_severity: str = "high"


class ArgusAlerter:
    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or self._load_config()

    def _load_config(self) -> AlertConfig:
        cfg = AlertConfig()
        cfg.telegram_token = os.getenv("ARGUS_TELEGRAM_TOKEN", "")
        cfg.telegram_chat_id = os.getenv("ARGUS_TELEGRAM_CHAT_ID", "")
        cfg.discord_webhook = os.getenv("ARGUS_DISCORD_WEBHOOK", "")
        cfg.slack_webhook = os.getenv("ARGUS_SLACK_WEBHOOK", "")
        cfg.min_severity = os.getenv("ARGUS_ALERT_MIN_SEVERITY", "high")
        return cfg

    def is_configured(self) -> bool:
        return bool(self.config.telegram_token or self.config.discord_webhook or self.config.slack_webhook)

    def should_alert(self, severity: str) -> bool:
        order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        min_val = order.get(self.config.min_severity, 3)
        return order.get(severity.lower(), 0) >= min_val

    def send_alert(self, findings: List[Dict[str, Any]], target: str) -> Dict[str, bool]:
        results = {}
        critical = [f for f in findings if self.should_alert(f.get("severity", "info"))]
        if not critical:
            return {}

        message = self._build_message(critical, target)

        if self.config.telegram_token and self.config.telegram_chat_id:
            results["telegram"] = self._send_telegram(message)

        if self.config.discord_webhook:
            results["discord"] = self._send_webhook(self.config.discord_webhook, message)

        if self.config.slack_webhook:
            results["slack"] = self._send_webhook(self.config.slack_webhook, message)

        if results:
            sent_to = [k for k, v in results.items() if v]
            logger.info(f"🔔 Alert sent to {sent_to} for {len(critical)} critical findings")

        return results

    def _build_message(self, findings: List[Dict], target: str) -> str:
        lines = [f"🚨 *Argus Pentest Alert* — {target}", ""]
        for f in findings[:5]:
            sev_icon = {"critical": "🔥", "high": "⚠️", "medium": "📌", "low": "ℹ️", "info": "ℹ️"}
            icon = sev_icon.get(f.get("severity", "info"), "❓")
            title = f.get("title", "Unknown")
            cat = f.get("category", "")
            poc = f.get("proof_of_concept", "")
            lines.append(f"{icon} *[{f.get('severity', 'UNKNOWN').upper()}] {title}*")
            lines.append(f"   Category: {cat}")
            if poc:
                lines.append(f"   PoC: `{poc[:200]}`")
            lines.append("")

        lines.append(f"Full report: ./argus_results/")
        return "\n".join(lines)

    def _send_telegram(self, message: str) -> bool:
        import httpx
        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            r = httpx.post(url, json=payload, timeout=10)
            return r.status_code == 200
        except Exception as e:
            logger.debug(f"Telegram alert failed: {e}")
            return False

    def _send_webhook(self, webhook_url: str, message: str) -> bool:
        import httpx
        try:
            r = httpx.post(webhook_url, json={"content": message}, timeout=10)
            return r.status_code in (200, 204)
        except Exception as e:
            logger.debug(f"Webhook alert failed: {e}")
            return False


_alerter_instance: Optional[ArgusAlerter] = None


def get_alerter() -> ArgusAlerter:
    global _alerter_instance
    if _alerter_instance is None:
        _alerter_instance = ArgusAlerter()
    return _alerter_instance
