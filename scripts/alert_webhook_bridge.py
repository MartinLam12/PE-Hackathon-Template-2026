#!/usr/bin/env python3
"""Receive Alertmanager webhooks and forward formatted alerts to Discord/Slack."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.alerting import deliver_alert_webhook


class AlertHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

    def do_POST(self) -> None:
        if self.path != "/alert":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        webhook = os.environ.get("ALERT_WEBHOOK_URL")
        status, response_body = deliver_alert_webhook(webhook, payload)
        if status >= 400:
            sys.stderr.write("webhook delivery failed\n")

        self.send_response(status)
        self.end_headers()
        self.wfile.write(response_body)


def main() -> None:
    """Start the Alertmanager webhook bridge HTTP server."""
    host = os.environ.get("WEBHOOK_BRIDGE_HOST", "0.0.0.0")
    port = int(os.environ.get("WEBHOOK_BRIDGE_PORT", "5002"))
    server = HTTPServer((host, port), AlertHandler)
    sys.stderr.write(f"alert webhook bridge listening on {host}:{port}\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
