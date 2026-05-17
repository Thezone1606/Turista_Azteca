#!/usr/bin/env bash
set -u
MAC="40:B8:2C:F8:53:80"
MAX_TRIES=30
SLEEP=5

is_connected() {
  bluetoothctl info "$MAC" 2>/dev/null | grep -q "Connected: yes"
}

bluetoothctl power on >/dev/null 2>&1 || true

for i in $(seq 1 "$MAX_TRIES"); do
  if is_connected; then
    echo "[$(date -Is)] Mobo connected (try $i)."
    exit 0
  fi
  bluetoothctl connect "$MAC" >/dev/null 2>&1 || true
  sleep "$SLEEP"
done

echo "[$(date -Is)] Failed to connect after $MAX_TRIES tries." >&2
exit 1
