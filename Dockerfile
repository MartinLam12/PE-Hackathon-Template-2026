FROM python:3.13-slim

# procps gives us ps/kill inside the container. They are not needed to serve
# traffic, but without them you cannot inspect or signal processes during an
# incident — see chaos/chaos_test.sh and docs/failure-modes.md.
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev

EXPOSE 5000

# gthread workers: requests are I/O bound (Postgres + Redis round trips), so
# threads let one worker overlap many in-flight requests. With 2 sync workers
# an instance could only ever handle 2 concurrent requests. Tunable via env so
# the load test can be re-run at different settings without a rebuild.
ENV GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=8

# exec the venv's gunicorn directly rather than going through `uv run`, so the
# gunicorn master is PID 1. That gets it SIGTERM on `docker stop` (graceful
# shutdown) and makes "kill PID 1" a genuine process-death chaos test.
CMD ["sh", "-c", "exec /app/.venv/bin/gunicorn -b 0.0.0.0:5000 -k gthread -w ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --worker-tmp-dir /dev/shm --access-logfile - run:app"]
