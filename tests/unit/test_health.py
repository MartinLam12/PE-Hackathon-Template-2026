"""Unit test for the /health endpoint.

Verifies the liveness-check endpoint (used by load balancers, uptime
monitors, etc.) returns 200 with the expected status payload,
independent of database state.
"""


def test_health_returns_ok(client):
    """GET /health responds 200 with a static {"status": "ok"} payload."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
