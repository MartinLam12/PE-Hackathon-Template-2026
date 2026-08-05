"""Locust load tests for the URL shortener.

Two workloads live here.

`ShortenerUser` is the original mixed workload used for the Bronze and
Silver runs. It is deliberately unchanged so the Bronze -> Silver -> Gold
numbers stay comparable across tiers:

    uv run locust -f loadtest/locustfile.py ShortenerUser \
      --host http://localhost:8080 --headless -u 500 -r 50 --run-time 60s

`RealisticUser` models how a URL shortener is actually used: overwhelmingly
redirects on short codes that already exist, with occasional browsing and
the rare create. `ShortenerUser` only ever redirects to a code it just
created, so every one of its redirects is a guaranteed cache miss — no use
for measuring what caching buys. This class drives the cache A/B in
docs/performance.md:

    uv run locust -f loadtest/locustfile.py RealisticUser \
      --host http://localhost:8080 --headless -u 500 -r 50 --run-time 60s

Every run is checked against pass/fail thresholds when it finishes and
exits non-zero if it missed them — see `_enforce_thresholds` below.
Override with `LOADTEST_MAX_FAIL_RATIO` and `LOADTEST_MAX_P95_MS`.
"""

import logging
import os
import random

from locust import HttpUser, between, constant, events, task
from locust.runners import WorkerRunner

# --- Pass/fail thresholds -------------------------------------------------
#
# k6 has these built in; Locust does not, so we assert on the totals when the
# run finishes and set a non-zero exit code if it missed. Without this a load
# test only ever "passes" — someone has to read the numbers and notice. With
# it, `uv run locust ...` can gate a pipeline the same way pytest does.
#
# The error-rate ceiling is the Scalability Gold criterion (under 5%). The p95
# ceiling is ours, set well above the ~4 ms we actually observe so it catches
# a regression rather than normal variance.

MAX_FAIL_RATIO = float(os.environ.get("LOADTEST_MAX_FAIL_RATIO", "0.05"))
MAX_P95_MS = float(os.environ.get("LOADTEST_MAX_P95_MS", "500"))


@events.quitting.add_listener
def _enforce_thresholds(environment, **_kwargs):
    """Fail the run if it missed its error-rate or latency targets."""
    # With --processes, this event fires in every worker as well as the
    # master. Only the master has the aggregated totals; a worker would see
    # an empty set and wrongly report "no requests were made".
    if isinstance(environment.runner, WorkerRunner):
        return

    stats = environment.stats.total
    breaches = []

    if stats.num_requests == 0:
        breaches.append("no requests were made")
    else:
        if stats.fail_ratio > MAX_FAIL_RATIO:
            breaches.append(
                f"error rate {stats.fail_ratio:.3%} exceeds {MAX_FAIL_RATIO:.3%}"
            )
        p95 = stats.get_response_time_percentile(0.95)
        if p95 > MAX_P95_MS:
            breaches.append(f"p95 {p95:.0f}ms exceeds {MAX_P95_MS:.0f}ms")

        # Check each endpoint too, not just the total. A seeding bug once had
        # 11% of POSTs failing while the aggregate sat at 0.23% — comfortably
        # inside the ceiling, and invisible. One broken endpoint drowned in a
        # sea of healthy redirects is exactly what an average hides.
        for entry in environment.stats.entries.values():
            if entry.num_requests and entry.fail_ratio > MAX_FAIL_RATIO:
                breaches.append(
                    f"{entry.method} {entry.name} error rate "
                    f"{entry.fail_ratio:.3%} exceeds {MAX_FAIL_RATIO:.3%}"
                )

    if breaches:
        logging.error("THRESHOLDS FAILED: %s", "; ".join(breaches))
        environment.process_exit_code = 1
    else:
        logging.info(
            "Thresholds passed: %d requests, %.3f%% errors, p95 %.0fms",
            stats.num_requests,
            stats.fail_ratio * 100,
            stats.get_response_time_percentile(0.95),
        )
        environment.process_exit_code = 0


class ShortenerUser(HttpUser):
    """Original mixed workload. Kept stable for cross-tier comparison."""

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


class RealisticUser(HttpUser):
    """Read-heavy workload: mostly clicks on links that already exist."""

    wait_time = between(0.1, 1)
    # Short codes discovered at start-up, shared by every simulated user.
    codes = []

    def on_start(self):
        """Learn some existing short codes to redirect against."""
        if RealisticUser.codes:
            return

        response = self.client.get("/urls?limit=200", name="/urls [warmup]")
        if response.status_code == 200:
            RealisticUser.codes = [row["short_code"] for row in response.json()]

    @task(90)
    def redirect_existing(self):
        """The hot path: a click on a short link that already exists."""
        if not RealisticUser.codes:
            return
        code = random.choice(RealisticUser.codes)
        self.client.get(
            f"/{code}",
            name="/<short_code> [redirect]",
            allow_redirects=False,
        )

    @task(5)
    def browse(self):
        self.client.get("/urls?limit=50", name="/urls [list]")

    @task(3)
    def detail(self):
        if not RealisticUser.codes:
            return
        code = random.choice(RealisticUser.codes)
        self.client.get(f"/urls/{code}", name="/urls/<short_code> [detail]")

    @task(2)
    def create(self):
        self.client.post(
            "/urls",
            json={"original_url": "https://example.com/load-test"},
            name="/urls [POST]",
        )


class SaturationUser(RealisticUser):
    """Same request mix as RealisticUser, but with zero think time.

    With `between(0.1, 1)` think time, 500 simulated users can only ever
    generate about 900 requests/second no matter how fast the service is —
    the *load generator* is the limit and the service is never stressed.
    Removing think time pushes until something actually gives, which is the
    only way to see what caching is worth. Run it with several Locust
    processes so the generator does not become the bottleneck instead:

        uv run locust -f loadtest/locustfile.py SaturationUser \
          --host http://localhost:8080 --processes 4 \
          --headless -u 200 -r 50 --run-time 60s
    """

    wait_time = constant(0)
