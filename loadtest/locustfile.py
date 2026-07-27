"""Locust load test for the URL shortener.

Run against a live instance, e.g.:
    uv run locust -f loadtest/locustfile.py --host http://localhost:5000
"""

from locust import HttpUser, between, task


class ShortenerUser(HttpUser):
    wait_time = between(0.1, 1)

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(2)
    def list_urls(self):
        self.client.get("/urls")

    @task(1)
    def create_and_redirect(self):
        response = self.client.post(
            "/urls",
            json={"original_url": "https://example.com/load-test"},
            name="/urls [POST]",
        )
        if response.status_code == 201:
            short_code = response.json()["short_code"]
            self.client.get(
                f"/{short_code}",
                name="/<short_code> [redirect]",
                allow_redirects=False,
            )
