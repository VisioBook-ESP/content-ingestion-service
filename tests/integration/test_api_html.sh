#!/bin/bash
# Usage:
#   ./test_api_html.sh [host]                  # https://host (default: visiobook.cloud)
#   PROTOCOL=http ./test_api_html.sh localhost:8090
#   DEBUG=1 ./test_api_html.sh                 # verbose curl output

IP=${1:-${API_HOST:-visiobook.cloud}}
PROTOCOL=${PROTOCOL:-https}
BASE=$PROTOCOL://$IP
DEBUG=${DEBUG:-0}
PASS=0
FAIL=0
SKIP=0

# ── Colors ────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  C_RESET='\033[0m'
  C_GREEN='\033[0;32m'
  C_RED='\033[0;31m'
  C_YELLOW='\033[0;33m'
  C_CYAN='\033[0;36m'
  C_BOLD='\033[1m'
  C_DIM='\033[2m'
else
  C_RESET='' C_GREEN='' C_RED='' C_YELLOW='' C_CYAN='' C_BOLD='' C_DIM=''
fi

log_section() { echo -e "\n${C_BOLD}${C_CYAN}══════  $1  ══════${C_RESET}"; }
log_ok()      { echo -e "  ${C_GREEN}✔ PASS${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_fail()    { echo -e "  ${C_RED}✘ FAIL${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_skip()    { echo -e "  ${C_YELLOW}⊘ SKIP${C_RESET}  $1"; }
log_warn()    { echo -e "  ${C_YELLOW}⚠ WARN${C_RESET}  $1"; }
log_info()    { echo -e "  ${C_DIM}ℹ $1${C_RESET}"; }

do_curl() {
  local label="$1"; shift
  local -a args=("$@")
  local raw
  raw=$(curl --connect-timeout 5 --max-time 30 -s \
             -w "\n%{http_code}\n%{time_total}" \
             "${args[@]}" 2>/dev/null)
  BODY=$(echo "$raw" | head -n -2)
  CODE=$(echo "$raw" | tail -n 2 | head -n 1)
  ELAPSED=$(echo "$raw" | tail -n 1 | awk '{printf "%d", $1*1000}')
}

check() {
  local label="$1"
  if [ "$CODE" -ge 200 ] && [ "$CODE" -lt 300 ] 2>/dev/null; then
    log_ok "$label" "$CODE" "$ELAPSED"
    [ -n "$BODY" ] && echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    PASS=$((PASS + 1))
    echo ""
  else
    log_fail "$label" "$CODE" "$ELAPSED"
    [ "$CODE" = "000" ] && log_warn "Cannot connect to $BASE"
    [ -n "$BODY" ] && echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /' || echo "    $BODY"
    FAIL=$((FAIL + 1))
    echo ""
    echo -e "  ${C_RED}${C_BOLD}Test stopped at: $label${C_RESET}"
    print_summary
    exit 1
  fi
}

# Poll job status until completed/failed or timeout
poll_job() {
  local job_id="$1"
  local max_attempts=20
  local attempt=0
  local status=""

  log_info "Polling job $job_id..." >&2
  while [ $attempt -lt $max_attempts ]; do
    sleep 2
    attempt=$((attempt + 1))
    do_curl "GET /ingest/status/$job_id" \
      "${AUTH_HEADER[@]}" \
      "$BASE/api/v1/ingest/status/$job_id"
    status=$(echo "$BODY" | jq -r '.status // empty' 2>/dev/null)
    log_info "Attempt $attempt/$max_attempts — status: $status" >&2
    if [ "$status" = "completed" ] || [ "$status" = "failed" ]; then
      break
    fi
  done
  echo "$status"
}

print_summary() {
  echo ""
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
  [ $PASS -gt 0 ] && echo -e "  ${C_GREEN}✔ $PASS passed${C_RESET}"
  [ $FAIL -gt 0 ] && echo -e "  ${C_RED}✘ $FAIL failed${C_RESET}"
  [ $SKIP -gt 0 ] && echo -e "  ${C_YELLOW}⊘ $SKIP skipped${C_RESET}"
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
}

# ── Bootstrap ─────────────────────────────────────────────────────────────────
echo -e "${C_BOLD}Target: ${C_CYAN}$BASE${C_RESET}"

if [ -f /tmp/esp_test_token ]; then
  TOKEN=$(cat /tmp/esp_test_token)
  echo -e "${C_DIM}Token : ${TOKEN:0:40}...${C_RESET}"
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
else
  log_warn "No token found — run test_api_user_core.sh first"
  exit 1
fi

# ── Create test HTML file ──────────────────────────────────────────────────────
HTML_FILE=$(mktemp /tmp/test-html-XXXX.html)
cat > "$HTML_FILE" <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HTML Test Document</title>
</head>
<body>
  <h1>HTML Ingestion Test</h1>
  <p>This is the first paragraph of the HTML test document.</p>
  <p>It contains multiple sentences to verify text extraction and chunking.</p>
  <h2>Section 2</h2>
  <p>Second section with additional content for ingestion validation.</p>
  <ul>
    <li>Item one</li>
    <li>Item two</li>
    <li>Item three</li>
  </ul>
</body>
</html>
EOF

trap "rm -f $HTML_FILE" EXIT

# ── HTML Upload + Ingest ───────────────────────────────────────────────────────
log_section "HTML — Upload & Ingest"

do_curl "POST /upload/ (HTML)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/upload/" \
  -F "file=@$HTML_FILE;filename=test-doc.html" \
  -F "project_id=test-html-project"
check "POST /api/v1/upload/ (HTML)"

HTML_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)

if [ -z "$HTML_FILE_ID" ]; then
  log_warn "No fileId returned — skipping ingest"
  SKIP=$((SKIP + 1))
  print_summary
  exit 0
fi

do_curl "POST /ingest/ (HTML)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/ingest/" \
  -H "Content-Type: application/json" \
  -d "{
    \"fileId\": \"$HTML_FILE_ID\",
    \"projectId\": \"test-html-project\",
    \"options\": {\"cleanText\": true, \"extractMetadata\": true, \"chunkSize\": 1000, \"overlap\": 0}
  }"
check "POST /api/v1/ingest/ (HTML)"

JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)
if [ -n "$JOB_ID" ]; then
  FINAL_STATUS=$(poll_job "$JOB_ID")
  do_curl "GET /ingest/status/$JOB_ID (HTML final)" \
    "${AUTH_HEADER[@]}" \
    "$BASE/api/v1/ingest/status/$JOB_ID"
  if [ "$FINAL_STATUS" = "completed" ]; then
    log_ok "HTML ingest — job completed" "$CODE" "$ELAPSED"
    echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    PASS=$((PASS + 1))
  else
    log_fail "HTML ingest — job $FINAL_STATUS" "$CODE" "$ELAPSED"
    echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  fi
  echo ""
fi

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary
