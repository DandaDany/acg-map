#!/bin/bash
# LaunchAgent entrypoint for the exhibition map update.
# Adds observable logging and a simple lock around update_all.py.
set -u

DIR="/Users/daniel0522/Desktop/Claude playground/全台展覽地圖"
PY="/Users/daniel0522/miniforge3/bin/python3"
LOG="$DIR/runtime/logs/scheduled_update.log"
LOCKDIR="$DIR/runtime/state/scheduled_update.lock"
LAST_SUCCESS="$DIR/runtime/state/scheduled_update.last_success"
SKIP_WINDOW_SECONDS=21600
mkdir -p "$DIR/runtime/logs" "$DIR/runtime/state"

{
  echo ""
  echo "=== launchd entered $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  echo "uid=$(id -u) user=$(id -un)"
	  echo "python=$PY"
	  "$PY" --version
	  echo "cwd=$DIR"

	  if [ -f "$LAST_SUCCESS" ]; then
	    now=$(date +%s)
	    last=$(stat -f %m "$LAST_SUCCESS" 2>/dev/null || echo 0)
	    age=$((now - last))
	    if [ "$age" -ge 0 ] && [ "$age" -lt "$SKIP_WINDOW_SECONDS" ]; then
	      echo "SKIP: last successful update was ${age}s ago at $LAST_SUCCESS"
	      echo "=== launchd finished $(date '+%Y-%m-%d %H:%M:%S %Z') exit=0 ==="
	      exit 0
	    fi
	  fi

	  if ! mkdir "$LOCKDIR" 2>/dev/null; then
	    echo "SKIP: update lock exists at $LOCKDIR"
    echo "=== launchd finished $(date '+%Y-%m-%d %H:%M:%S %Z') exit=75 ==="
    exit 75
  fi
  trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

  cd "$DIR" || {
    code=$?
    echo "ERR: cannot cd to $DIR"
    echo "=== launchd finished $(date '+%Y-%m-%d %H:%M:%S %Z') exit=$code ==="
    exit "$code"
  }

	  "$PY" -u backend/update_all.py
	  code=$?
	  if [ "$code" -eq 0 ]; then
	    touch "$LAST_SUCCESS"
	  fi
	  echo "=== launchd finished $(date '+%Y-%m-%d %H:%M:%S %Z') exit=$code ==="
  exit "$code"
} >> "$LOG" 2>&1
