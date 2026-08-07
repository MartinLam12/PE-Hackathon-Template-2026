#!/usr/bin/env python3
"""Poll /health and send a webhook alert when the service is unhealthy.

Incident Response — Silver backup path. Set ALERT_WEBHOOK_URL to a Discord or
Slack incoming webhook URL, then run:

    uv run python scripts/health_watch.py --url http://localhost:8080/health

Exit codes: 0 = healthy, 1 = unhealthy (and alert sent if configured).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime


def check_health(url: str, timeout: float) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            if response.status != 200:
                return False, f"HTTP {response.status}: {body[:200]}"
            return True, body
    except urllib.error.URLError as exc:
        return False, str(exc.reason)


def send_alert(webhook_url: str, message: str) -> None:
    payload = json.dumps({"content": message}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check watcher with optional webhook alert")
    parser.add_argument("--url", default="http://127.0.0.1:8080/health", help="Health check URL")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    parser.add_argument(
        "--webhook",
        default=None,
        help="Discord/Slack webhook URL (or set ALERT_WEBHOOK_URL)",
    )
    args = parser.parse_args()

    import os

    webhook = args.webhook or os.environ.get("ALERT_WEBHOOK_URL")
    ok, detail = check_health(args.url, args.timeout)

    if ok:
        print(f"OK {args.url} -> {detail.strip()}")
        return 0

    timestamp = datetime.now(UTC).isoformat()
    message = f"[ALERT {timestamp}] Health check failed for {args.url}: {detail}"
    print(message, file=sys.stderr)

    if webhook:
        try:
            send_alert(webhook, message)
            print("Alert sent.", file=sys.stderr)
        except urllib.error.URLError as exc:
            print(f"Failed to send alert: {exc.reason}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
