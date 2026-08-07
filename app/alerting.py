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


def chat_webhook_payload(webhook_url: str, message: str) -> dict[str, str]:
    """Build the JSON body for Discord or Slack incoming webhooks."""
    truncated = message[:1900]
    if "hooks.slack.com" in webhook_url:
        return {"text": truncated}
    return {"content": truncated}


def send_chat_webhook(webhook_url: str, message: str) -> None:
    """POST a formatted alert to a Discord or Slack incoming webhook URL."""
    payload = json.dumps(chat_webhook_payload(webhook_url, message)).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        pass


def deliver_alert_webhook(webhook_url: str | None, payload: dict) -> tuple[int, bytes]:
    """Forward an Alertmanager payload to chat; return HTTP status and body."""
    message = format_alertmanager_payload(payload)
    if not webhook_url:
        return 200, b"ok"

    try:
        send_chat_webhook(webhook_url, message)
    except urllib.error.URLError:
        return 502, b"webhook delivery failed\n"

    return 200, b"ok\n"
