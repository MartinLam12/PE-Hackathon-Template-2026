"""Unit tests for Alertmanager → chat webhook formatting."""

from unittest.mock import MagicMock, patch

from app.alerting import format_alertmanager_payload, send_chat_webhook


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


@patch("app.alerting.urllib.request.urlopen")
def test_send_chat_webhook_posts_json(mock_urlopen: MagicMock):
    mock_urlopen.return_value.__enter__.return_value = MagicMock()

    send_chat_webhook("https://example.com/webhook", "hello alert")

    mock_urlopen.assert_called_once()
    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://example.com/webhook"
    assert request.method == "POST"
    assert b"hello alert" in request.data
