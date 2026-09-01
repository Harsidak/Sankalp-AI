#!/usr/bin/env bash
# Restart the dev API on port 8000.
#
# uvicorn --reload proved unreliable on Windows here: a worker that outlives
# its reloader keeps the socket, and every later start is silently shadowed by
# the stale process still answering on 8000. This kills whatever holds the
# port first, so a restart is always a real restart.
set -u
cd "$(dirname "$0")"

for pid in $(netstat -ano | grep LISTENING | grep ':8000 ' | awk '{print $NF}' | sort -u); do
  echo "stopping pid $pid"
  taskkill //PID "$pid" //T //F >/dev/null 2>&1 || true
done
sleep 1

./.venv/Scripts/uvicorn.exe app.main:app --port 8000 --host 127.0.0.1
