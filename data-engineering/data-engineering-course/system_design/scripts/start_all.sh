#!/usr/bin/env bash
# Start every system design service in the background.
#
# Usage:
#     bash scripts/start_all.sh
#     bash scripts/start_all.sh stop
#     bash scripts/start_all.sh status
#
# Each service binds to a unique port (8001-8039). Logs go to var/logs/.

set -uo pipefail

cd "$(dirname "$0")/.."
mkdir -p var/logs var/pids

# module_name:default_port
SERVICES=(
  "00_overview:8100"
  "01_url_shortener:8001"
  "02_typeahead:8002"
  "03_instagram:8003"
  "04_twitter:8004"
  "05_newsfeed:8005"
  "06_yt_or_netflix:8006"
  "07_message_queue:8007"
  "08_webhook_delivery:8008"
  "09_uber_eats:8009"
  "10_web_crawler:8010"
  "11_job_scheduler:8011"
  "12_user_data_export:8012"
  "13_kv_store:8013"
  "14_rate_limiter:8014"
  "15_distributed_lru:8015"
  "16_dropbox:8016"
  "17_s3_storage:8017"
  "18_ticketmaster:8018"
  "19_hotel_booking:8019"
  "20_parking_garage:8020"
  "21_metrics_logging:8021"
  "22_apm:8022"
  "23_doc_processing:8023"
  "24_zillow:8024"
  "25_weather_app:8025"
  "26_messenger:8026"
  "27_whatsapp:8027"
  "28_chess:8028"
  "29_slack:8029"
  "30_google_docs:8030"
  "31_tiktok:8031"
  "32_twitch:8032"
  "33_ai_support:8033"
  "34_chatgpt:8034"
  "35_file_uploader:8035"
  "36_llm_batching:8036"
  "37_claude_code:8037"
  "38_voice_ai:8038"
  "39_reddit_homepage:8039"
)

start_one() {
  local name="$1"
  local port="$2"
  local pidfile="var/pids/${name}.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "  ${name} already running (pid $(cat "$pidfile"))"
    return
  fi
  if [[ ! -f "${name}/code/app.py" ]]; then
    echo "  ${name} skipped (no code/app.py)"
    return
  fi
  PORT="$port" nohup python3 "${name}/code/app.py" > "var/logs/${name}.log" 2>&1 &
  echo $! > "$pidfile"
  echo "  ${name} started on :${port} (pid $!)"
}

stop_one() {
  local name="$1"
  local pidfile="var/pids/${name}.pid"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "  ${name} stopped (pid $pid)"
    fi
    rm -f "$pidfile"
  fi
}

status_one() {
  local name="$1"
  local port="$2"
  local pidfile="var/pids/${name}.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    printf "  %-25s :%s  UP   pid=%s\n" "$name" "$port" "$(cat "$pidfile")"
  else
    printf "  %-25s :%s  DOWN\n" "$name" "$port"
  fi
}

cmd="${1:-start}"

case "$cmd" in
  start)
    echo "Starting ${#SERVICES[@]} services..."
    for s in "${SERVICES[@]}"; do
      start_one "${s%:*}" "${s#*:}"
    done
    echo "Logs: var/logs/<service>.log"
    echo "Stop: bash scripts/start_all.sh stop"
    ;;
  stop)
    echo "Stopping all services..."
    for s in "${SERVICES[@]}"; do
      stop_one "${s%:*}"
    done
    ;;
  status)
    for s in "${SERVICES[@]}"; do
      status_one "${s%:*}" "${s#*:}"
    done
    ;;
  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}" >&2
    exit 1
    ;;
esac
