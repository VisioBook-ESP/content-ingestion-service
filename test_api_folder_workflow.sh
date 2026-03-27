#!/bin/bash
# Test: folder-per-user workflow
#
# Validates that:
#   1. First upload auto-creates a folderId in DB for the user
#   2. Second upload reuses the same folderId
#   3. GET /folders/files returns both files under that folderId
#
# Usage:
#   ./test_api_folder_workflow.sh [host]
#   PROTOCOL=http ./test_api_folder_workflow.sh localhost:8090
#   DEBUG=1 ./test_api_folder_workflow.sh
#
# Requires: test_api_user_core.sh to have been run first (token in /tmp/esp_test_token)

IP=${1:-${API_HOST:-visiobook.cloud}}
PROTOCOL=${PROTOCOL:-https}
BASE=$PROTOCOL://$IP
DEBUG=${DEBUG:-0}
PASS=0
FAIL=0

# ── Colors ─────────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  C_RESET='\033[0m'; C_GREEN='\033[0;32m'; C_RED='\033[0;31m'
  C_YELLOW='\033[0;33m'; C_CYAN='\033[0;36m'; C_BOLD='\033[1m'; C_DIM='\033[2m'
else
  C_RESET=''; C_GREEN=''; C_RED=''; C_YELLOW=''; C_CYAN=''; C_BOLD=''; C_DIM=''
fi

log_section() { echo -e "\n${C_BOLD}${C_CYAN}══════  $1  ══════${C_RESET}"; }
log_ok()      { echo -e "  ${C_GREEN}✔ PASS${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_fail()    { echo -e "  ${C_RED}✘ FAIL${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_warn()    { echo -e "  ${C_YELLOW}⚠ WARN${C_RESET}  $1"; }
log_info()    { echo -e "  ${C_DIM}ℹ $1${C_RESET}"; }

do_curl() {
  local label="$1"; shift
  local raw
  raw=$(curl --connect-timeout 5 --max-time 30 -s \
             -w "\n%{http_code}\n%{time_total}" \
             "$@" 2>/dev/null)
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
    print_summary
    exit 1
  fi
}

# Global return values (avoids subshell issues with command substitution)
LAST_FILE_ID=""
LAST_STATUS=""

poll_job() {
  local job_id="$1"
  local max_attempts=20
  local attempt=0

  LAST_STATUS=""
  log_info "Polling job $job_id..."
  while [ $attempt -lt $max_attempts ]; do
    sleep 2
    attempt=$((attempt + 1))
    do_curl "poll" "${AUTH_HEADER[@]}" "$BASE/api/v1/ingest/status/$job_id"
    LAST_STATUS=$(echo "$BODY" | jq -r '.status // empty' 2>/dev/null)
    log_info "Attempt $attempt/$max_attempts — status: $LAST_STATUS"
    if [ "$LAST_STATUS" = "completed" ] || [ "$LAST_STATUS" = "failed" ]; then
      break
    fi
  done
}

print_summary() {
  echo ""
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
  [ $PASS -gt 0 ] && echo -e "  ${C_GREEN}✔ $PASS passed${C_RESET}"
  [ $FAIL -gt 0 ] && echo -e "  ${C_RED}✘ $FAIL failed${C_RESET}"
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
}

upload_and_ingest() {
  local label="$1"
  local file="$2"
  local project_id="$3"

  LAST_FILE_ID=""

  do_curl "POST /upload/ ($label)" \
    "${AUTH_HEADER[@]}" \
    -X POST "$BASE/api/v1/upload/" \
    -F "file=@$file;filename=${label}.txt" \
    -F "project_id=$project_id"
  check "POST /api/v1/upload/ ($label)"

  LAST_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty')
  if [ -z "$LAST_FILE_ID" ]; then
    log_warn "No fileId — aborting"
    print_summary; exit 1
  fi

  do_curl "POST /ingest/ ($label)" \
    "${AUTH_HEADER[@]}" \
    -X POST "$BASE/api/v1/ingest/" \
    -H "Content-Type: application/json" \
    -d "{\"fileId\":\"$LAST_FILE_ID\",\"projectId\":\"$project_id\",\"options\":{\"cleanText\":true,\"extractMetadata\":false,\"chunkSize\":500,\"overlap\":0}}"
  check "POST /api/v1/ingest/ ($label)"

  local job_id
  job_id=$(echo "$BODY" | jq -r '.jobId // empty')
  if [ -n "$job_id" ]; then
    poll_job "$job_id"
    if [ "$LAST_STATUS" = "completed" ]; then
      log_ok "$label ingest — job completed" "200" "0"
      PASS=$((PASS + 1))
    else
      log_fail "$label ingest — job $LAST_STATUS" "200" "0"
      FAIL=$((FAIL + 1))
      print_summary; exit 1
    fi
    echo ""
  fi
}

# ── Bootstrap ──────────────────────────────────────────────────────────────────
echo -e "${C_BOLD}Target: ${C_CYAN}$BASE${C_RESET}"

if [ -f /tmp/esp_test_token ]; then
  TOKEN=$(cat /tmp/esp_test_token)
  echo -e "${C_DIM}Token : ${TOKEN:0:40}...${C_RESET}"
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
else
  log_warn "No token — run ./test_api_user_core.sh first"
  exit 1
fi

# ── Create two minimal text files ──────────────────────────────────────────────
FILE1=$(mktemp /tmp/folder-test-XXXX.txt)
FILE2=$(mktemp /tmp/folder-test-XXXX.txt)
echo "First document for folder workflow test. Contains enough text to be ingested." > "$FILE1"
echo "Second document for folder workflow test. Should land in the same folder as the first." > "$FILE2"
trap "rm -f $FILE1 $FILE2" EXIT

# ── Test 1: first upload — folderId should be created ─────────────────────────
log_section "Upload 1 — folderId creation"
upload_and_ingest "file-1" "$FILE1" "folder-workflow-test"
FILE1_ID="$LAST_FILE_ID"

# ── Test 2: second upload — folderId should be reused ─────────────────────────
log_section "Upload 2 — folderId reuse"
upload_and_ingest "file-2" "$FILE2" "folder-workflow-test"
FILE2_ID="$LAST_FILE_ID"

# ── Test 3: GET /folders/files — both files under the same folderId ───────────
log_section "GET /folders/files — verify same folder"
do_curl "GET /api/v1/folders/files" \
  "${AUTH_HEADER[@]}" \
  "$BASE/api/v1/folders/files"
check "GET /api/v1/folders/files"

FOLDER_ID=$(echo "$BODY" | jq -r '.folderId // empty')
COUNT=$(echo "$BODY" | jq -r '.count // 0')

if [ -z "$FOLDER_ID" ]; then
  log_warn "No folderId in response"
  FAIL=$((FAIL + 1))
else
  log_info "folderId: $FOLDER_ID"
  log_info "Total files in folder: $COUNT"
fi

# Verify both fileIds appear in the response
for fid in "$FILE1_ID" "$FILE2_ID"; do
  if echo "$BODY" | jq -r '.files[].fileId // .files[]?.fileId' 2>/dev/null | grep -Fq "$fid"; then
    log_ok "File $fid present in folder" "—" "—"
    PASS=$((PASS + 1))
  else
    log_warn "File $fid NOT found in folder response"
    FAIL=$((FAIL + 1))
  fi
done

# ── Summary ────────────────────────────────────────────────────────────────────
print_summary
