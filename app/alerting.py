"""Alert formatting helpers for webhook delivery."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def format_alertmanager_payload(payload: dict) -> str:
    """Turn an Alertmanager webhook body into a human-readable chat message."""
    status = payload.get("status", "unknown")
    alerts = payload.get("alerts", [])
    lines = [f"[Alertmanager {status.upper()}] {len(alerts)} alert(s)"]

    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        name = labels.get("alertname", "unknown")
        severity = labels.get("severity", "info")
        summary = annotations.get("summary", "")
        description = annotations.get("description", "")
        lines.append(f"• {name} ({severity}): {summary} — {description}")

    return "\n".join(lines)


def send_chat_webhook(webhook_url: str, message: str) -> None:
    payload = json.dumps({"content": message[:1900]}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        pass
