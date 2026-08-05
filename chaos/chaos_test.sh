#!/usr/bin/env bash
# Chaos / failure testing for the URL shortener.
#
# Runs three scenarios against the Docker Compose stack and prints a
# timestamped transcript. Redirect the output to chaos/results/ to keep
# the evidence:
#
#   docker compose up -d --build
#   docker compose exec -T app1 uv run seed.py
#   ./chaos/chaos_test.sh 2>&1 | tee chaos/results/chaos-run.log
#
# Scenarios:
#   A. App instance dies       -> LB degrades to survivor, container auto-restarts
#   B. Database goes away      -> API returns 503 JSON, /health stays 200
#   C. Gunicorn worker dies    -> master respawns it, no request is lost
#   D. Cache goes away         -> reads fall through to Postgres, still correct

set -uo pipefail

LB=http://localhost:8080
PROJECT=${COMPOSE_PROJECT_NAME:-pe-hackathon-template-2026}
APP1="${PROJECT}-app1-1"

ts()   { date -u +"%H:%M:%SZ"; }
say()  { echo; echo "=== $(ts)  $* ==="; }
note() { echo "  [$(ts)] $*"; }

status_of() { docker inspect "$1" --format '{{.State.Status}} exit={{.State.ExitCode}} restarts={{.RestartCount}}' 2>/dev/null; }
code_for()  { curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$1"; }
post_code() {
  curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
    -X POST -H 'Content-Type: application/json' \
    -d '{"original_url":"https://example.com/chaos"}' "$1"
}

# Poll the load balancer in the background, one line per request.
start_poller() {
  local out=$1
  : > "$out"
  (
    while :; do
      c=$(code_for "$LB/health")
      echo "$(ts) /health $c" >> "$out"
      sleep 0.2
    done
  ) &
  POLLER=$!
}
stop_poller() { kill "$POLLER" 2>/dev/null; wait "$POLLER" 2>/dev/null; }

report_poller() {
  local out=$1 total ok bad
  total=$(wc -l < "$out" | tr -d ' ')
  ok=$(grep -c ' 200$' "$out")
  bad=$((total - ok))
  note "poller: $total requests, $ok x 200, $bad non-200"
  if [ "$bad" -gt 0 ]; then
    note "non-200 responses observed:"
    grep -v ' 200$' "$out" | head -10 | sed 's/^/      /'
  fi
}

echo "############################################################"
echo "# Chaos test run: $(date -u +'%Y-%m-%d %H:%M:%SZ')"
echo "# Host: $(uname -srm)"
echo "############################################################"

say "Baseline"
docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'
note "GET $LB/health  -> $(code_for "$LB/health")"
note "GET $LB/urls    -> $(code_for "$LB/urls")"
note "load balancer is distributing across both instances:"
for _ in 1 2 3 4; do
  echo "      $(curl -s -o /dev/null -D - "$LB/health" | grep -i '^x-upstream-addr' | tr -d '\r')"
  sleep 1
done

# ---------------------------------------------------------------------------
say "Scenario A: kill the app process inside app1"
# ---------------------------------------------------------------------------
note "app1 before: $(status_of "$APP1")"
start_poller /tmp/chaos_poll_a.log
note "poller started against $LB (every 0.2s)"
sleep 2

note "killing PID 1 (the gunicorn master) inside app1 ..."
# Two traps here, both worth knowing before an incident:
#
#  1. `kill` is a shell builtin, not an executable, so it has to go through
#     `sh -c`. `docker compose exec app1 kill -9 1` fails with
#     "executable file not found in $PATH".
#
#  2. SIGKILL is NOT delivered to PID 1 from inside its own PID namespace —
#     the kernel shields a namespace's init process from signals sent by its
#     own members unless a handler is installed. `kill -9 1` therefore does
#     nothing at all. SIGQUIT works because gunicorn installs a handler for
#     it, and it makes the master exit abruptly, which is what we want.
docker compose exec -T app1 sh -c 'kill -QUIT 1' 2>&1 | sed 's/^/      /'
note "SIGQUIT sent to the gunicorn master"

sleep 2
note "app1 during outage: $(status_of "$APP1")"
note "service still answering through LB? GET /health -> $(code_for "$LB/health")"
note "service still answering through LB? GET /urls   -> $(code_for "$LB/urls")"

note "waiting for restart policy to bring app1 back ..."
for i in $(seq 1 30); do
  st=$(docker inspect "$APP1" --format '{{.State.Status}}' 2>/dev/null)
  hl=$(docker inspect "$APP1" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>/dev/null)
  if [ "$st" = "running" ] && [ "$hl" = "healthy" ]; then
    note "app1 healthy again after ~${i}s"
    break
  fi
  sleep 1
done
note "app1 after:  $(status_of "$APP1")"
note "restart policy: $(docker inspect "$APP1" --format '{{.HostConfig.RestartPolicy.Name}}')"

sleep 2
stop_poller
report_poller /tmp/chaos_poll_a.log
note "both upstreams back in rotation:"
for _ in 1 2 3 4; do
  echo "      $(curl -s -o /dev/null -D - "$LB/health" | grep -i '^x-upstream-addr' | tr -d '\r')"
  sleep 1
done

# ---------------------------------------------------------------------------
say "Scenario B: take the database away"
# ---------------------------------------------------------------------------
note "stopping postgres ..."
docker compose stop postgres >/dev/null 2>&1
sleep 3

note "GET /urls   -> $(code_for "$LB/urls")   (expect 503, not a crash)"
note "response body:"
curl -s --max-time 5 "$LB/urls" | head -c 300 | sed 's/^/      /'
echo
note "GET /health -> $(code_for "$LB/health")   (expect 200: health skips the DB)"
note "app containers still alive (did NOT crash):"
docker compose ps --format 'table {{.Name}}\t{{.Status}}' | grep -E 'app1|app2' | sed 's/^/      /'

note "restarting postgres ..."
docker compose start postgres >/dev/null 2>&1
for i in $(seq 1 30); do
  c=$(code_for "$LB/urls")
  if [ "$c" = "200" ]; then note "GET /urls recovered to 200 after ~${i}s"; break; fi
  sleep 1
done
note "final: GET /urls -> $(code_for "$LB/urls")"

# ---------------------------------------------------------------------------
say "Scenario C: kill a gunicorn worker (master should respawn it)"
# ---------------------------------------------------------------------------
gunicorn_count() { docker compose exec -T app1 sh -c "ps -eo pid,args | grep -c '[g]unicorn'" | tr -d ' \r'; }

before=$(gunicorn_count)
note "gunicorn processes in app1 before: $before  (1 master + workers)"
start_poller /tmp/chaos_poll_c.log
sleep 2

# PPID 1 = a worker forked by the gunicorn master (which is PID 1).
worker=$(docker compose exec -T app1 sh -c "ps -eo pid,ppid,args | grep '[g]unicorn' | awk '\$2 == 1 {print \$1; exit}'" | tr -d ' \r')
if [ -n "$worker" ]; then
  note "killing gunicorn worker PID $worker ..."
  docker compose exec -T app1 sh -c "kill -9 $worker" 2>&1 | sed 's/^/      /'
  sleep 5
  after=$(gunicorn_count)
  note "gunicorn processes in app1 after:  $after  (master respawns the worker)"
  note "container never exited: $(status_of "$APP1")"
else
  note "could not identify a worker PID; skipping"
fi
sleep 2
stop_poller
report_poller /tmp/chaos_poll_c.log

# ---------------------------------------------------------------------------
say "Scenario D: take Redis away (cache outage must not be an outage)"
# ---------------------------------------------------------------------------
code=$(curl -s "$LB/urls?limit=1" | sed -n 's/.*"short_code": *"\([^"]*\)".*/\1/p' | head -1)
note "using existing short code: ${code:-<none>}"
note "warming the cache: GET /$code -> $(code_for "$LB/$code")"

note "stopping redis ..."
docker compose stop redis >/dev/null 2>&1
sleep 3

start_poller /tmp/chaos_poll_d.log
sleep 2
note "with Redis down:"
note "  GET /$code (redirect) -> $(code_for "$LB/$code")   (expect 302 from Postgres)"
note "  GET /urls             -> $(code_for "$LB/urls")   (expect 200 from Postgres)"
note "  GET /urls/$code       -> $(code_for "$LB/urls/$code")   (expect 200 from Postgres)"
note "  POST /urls            -> $(post_code "$LB/urls")   (expect 201, writes do not need the cache)"
sleep 2
stop_poller
report_poller /tmp/chaos_poll_d.log

note "restarting redis ..."
docker compose start redis >/dev/null 2>&1
for i in $(seq 1 30); do
  if docker compose ps redis --format '{{.Status}}' | grep -q healthy; then
    note "redis healthy again after ~${i}s"; break
  fi
  sleep 1
done
note "after recovery: GET /$code -> $(code_for "$LB/$code")"
note "cache serving again: $(docker compose exec -T redis redis-cli INFO stats | grep keyspace_hits | tr -d '\r')"

say "Final state"
docker compose ps --format 'table {{.Name}}\t{{.Service}}\t{{.Status}}'
echo
echo "############################################################"
echo "# Chaos test complete: $(date -u +'%Y-%m-%d %H:%M:%SZ')"
echo "############################################################"
