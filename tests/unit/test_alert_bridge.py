"""Unit tests for Alertmanager → chat webhook formatting."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

from app.alerting import (
    chat_webhook_payload,
    deliver_alert_webhook,
    format_alertmanager_payload,
    send_chat_webhook,
)


def test_format_single_firing_alert():
    payload = {
        "status": "firing",
        "alerts": [
            {
                "labels": {"alertname": "ShortenerDown", "severity": "critical"},
                "annotations": {
                    "summary": "URL shortener is unreachable",
                    "description": "Prometheus cannot scrape /metrics",
                },
            }
        ],
    }

    message = format_alertmanager_payload(payload)

    assert "FIRING" in message
    assert "ShortenerDown" in message
    assert "critical" in message
    assert "URL shortener is unreachable" in message


def test_format_resolved_alert():
    payload = {
        "status": "resolved",
        "alerts": [
            {
                "labels": {"alertname": "HighErrorRate", "severity": "warning"},
                "annotations": {"summary": "High 5xx error rate", "description": "resolved"},
            }
        ],
    }

    message = format_alertmanager_payload(payload)

    assert "RESOLVED" in message
    assert "HighErrorRate" in message


def test_chat_webhook_payload_uses_content_for_discord():
    payload = chat_webhook_payload("https://discord.com/api/webhooks/abc", "hello")

    assert payload == {"content": "hello"}


def test_chat_webhook_payload_uses_text_for_slack():
    payload = chat_webhook_payload("https://hooks.slack.com/services/T/B/X", "hello")

    assert payload == {"text": "hello"}


def test_chat_webhook_payload_uses_text_for_uppercase_slack_host():
    payload = chat_webhook_payload("https://HOOKS.SLACK.COM/services/T/B/X", "hello")

    assert payload == {"text": "hello"}


def test_chat_webhook_payload_ignores_slack_host_embedded_in_discord_url():
    payload = chat_webhook_payload(
        "https://discord.com/api/webhooks/abc?note=hooks.slack.com",
        "hello",
    )

    assert payload == {"content": "hello"}


@patch("app.alerting.urllib.request.urlopen")
def test_send_chat_webhook_posts_discord_json(mock_urlopen: MagicMock):
    mock_urlopen.return_value.__enter__.return_value = MagicMock()

    send_chat_webhook("https://discord.com/api/webhooks/abc", "hello alert")

    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://discord.com/api/webhooks/abc"
    assert request.method == "POST"
    assert json.loads(request.data.decode()) == {"content": "hello alert"}


@patch("app.alerting.urllib.request.urlopen")
def test_send_chat_webhook_posts_slack_json(mock_urlopen: MagicMock):
    mock_urlopen.return_value.__enter__.return_value = MagicMock()

    send_chat_webhook("https://hooks.slack.com/services/T/B/X", "hello alert")

    request = mock_urlopen.call_args[0][0]
    assert json.loads(request.data.decode()) == {"text": "hello alert"}


def test_deliver_alert_webhook_ok_without_webhook():
    status, body = deliver_alert_webhook(None, {"status": "firing", "alerts": []})

    assert status == 200
    assert body == b"ok"


@patch("app.alerting.send_chat_webhook")
def test_deliver_alert_webhook_ok_when_delivery_succeeds(mock_send: MagicMock):
    status, body = deliver_alert_webhook(
        "https://discord.com/api/webhooks/abc",
        {"status": "firing", "alerts": []},
    )

    assert status == 200
    assert body == b"ok\n"
    mock_send.assert_called_once()


@patch("app.alerting.send_chat_webhook", side_effect=urllib.error.URLError("timeout"))
def test_deliver_alert_webhook_returns_502_on_failure(mock_send: MagicMock):
    status, body = deliver_alert_webhook(
        "https://discord.com/api/webhooks/abc",
        {"status": "firing", "alerts": []},
    )

    assert status == 502
    assert b"webhook delivery failed" in body
    mock_send.assert_called_once()
