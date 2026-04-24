#!/bin/bash
# Usage:
#   ./test_api.sh [host]                  # https://host (default: visiobook.cloud)
#   PROTOCOL=http ./test_api.sh localhost:8090
#   DEBUG=1 ./test_api.sh                 # verbose curl output

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

# ── Logging helpers ────────────────────────────────────────────────────────────
log_section() { echo -e "\n${C_BOLD}${C_CYAN}══════  $1  ══════${C_RESET}"; }
log_ok()      { echo -e "  ${C_GREEN}✔ PASS${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_fail()    { echo -e "  ${C_RED}✘ FAIL${C_RESET}  $1  ${C_DIM}(HTTP $2 — ${3}ms)${C_RESET}"; }
log_skip()    { echo -e "  ${C_YELLOW}⊘ SKIP${C_RESET}  $1"; }
log_warn()    { echo -e "  ${C_YELLOW}⚠ WARN${C_RESET}  $1"; }
log_dbg()     { [ "$DEBUG" = "1" ] && echo -e "  ${C_DIM}▸ $1${C_RESET}"; }

# ── curl wrapper ───────────────────────────────────────────────────────────────
# Returns: sets BODY, CODE, ELAPSED
do_curl() {
  local label="$1"; shift   # human label (for debug)
  local -a args=("$@")

  if [ "$DEBUG" = "1" ]; then
    echo -e "\n  ${C_DIM}curl ${args[*]}${C_RESET}"
    # verbose headers to stderr, body+code to stdout
    local raw
    raw=$(curl --connect-timeout 5 --max-time 15 -s \
               -w "\n%{http_code}\n%{time_total}" \
               --write-out "" \
               -v "${args[@]}" 2>&1)
    # split verbose (lines with < >) from actual response
    local verbose_lines body_lines
    # curl -v sends headers to stderr; with 2>&1 they're mixed — filter by prefix
    echo "$raw" | grep -E "^[<>*]" | sed "s/^/  ${C_DIM}/" | sed "s/$/${C_RESET}/"
    local clean
    clean=$(curl --connect-timeout 5 --max-time 15 -s \
                 -w "\n%{http_code}\n%{time_total}" \
                 "${args[@]}" 2>/dev/null)
    BODY=$(echo "$clean" | head -n -2)
    CODE=$(echo "$clean" | tail -n 2 | head -n 1)
    ELAPSED=$(echo "$clean" | tail -n 1 | awk '{printf "%d", $1*1000}')
  else
    local raw
    raw=$(curl --connect-timeout 5 --max-time 15 -s \
               -w "\n%{http_code}\n%{time_total}" \
               "${args[@]}" 2>/dev/null)
    BODY=$(echo "$raw" | head -n -2)
    CODE=$(echo "$raw" | tail -n 2 | head -n 1)
    ELAPSED=$(echo "$raw" | tail -n 1 | awk '{printf "%d", $1*1000}')
  fi
}

# ── check result ───────────────────────────────────────────────────────────────
check() {
  local label="$1"

  if [ "$CODE" -ge 200 ] && [ "$CODE" -lt 300 ] 2>/dev/null; then
    log_ok "$label" "$CODE" "$ELAPSED"
    if [ -n "$BODY" ]; then
      echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    fi
    PASS=$((PASS + 1))
    echo ""
  else
    log_fail "$label" "$CODE" "$ELAPSED"
    if [ "$CODE" = "000" ]; then
      log_warn "Cannot connect to $BASE — is the service running?"
    fi
    if [ -n "$BODY" ]; then
      echo -e "  ${C_DIM}Response body:${C_RESET}"
      echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /' || echo "    $BODY" | head -20
    else
      echo -e "  ${C_DIM}(empty response body)${C_RESET}"
      echo -e "  ${C_DIM}Hint: gateway may not route this service — check with:${C_RESET}"
      echo -e "  ${C_DIM}  curl -v -H 'Authorization: Bearer \$TOKEN' $BASE/api/v1/validate/ -X POST -F 'file=@/tmp/test.txt'${C_RESET}"
    fi
    FAIL=$((FAIL + 1))
    echo ""
    echo -e "  ${C_RED}${C_BOLD}Test stopped at: $label${C_RESET}"
    print_summary
    exit 1
  fi
}

print_summary() {
  echo ""
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
  [ $PASS  -gt 0 ] && echo -e "  ${C_GREEN}✔ $PASS passed${C_RESET}"
  [ $FAIL  -gt 0 ] && echo -e "  ${C_RED}✘ $FAIL failed${C_RESET}"
  [ $SKIP  -gt 0 ] && echo -e "  ${C_YELLOW}⊘ $SKIP skipped${C_RESET}"
  echo -e "${C_BOLD}══════════════════════════════════${C_RESET}"
}

# ── Bootstrap ─────────────────────────────────────────────────────────────────
echo -e "${C_BOLD}Target: ${C_CYAN}$BASE${C_RESET}"
echo -e "${C_DIM}Debug : ${DEBUG:-0}${C_RESET}"

if [ -f /tmp/esp_test_token ]; then
  TOKEN=$(cat /tmp/esp_test_token)
  echo -e "${C_DIM}Token : ${TOKEN:0:40}...${C_RESET}"
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
else
  log_warn "No token found — run test_api_user_core.sh first if auth is required"
  TOKEN=""
  AUTH_HEADER=()
fi

TMPFILE=$(mktemp /tmp/test-XXXX.txt)
echo "This is a test document for content ingestion. It contains some sample text to validate extraction and preprocessing features." > "$TMPFILE"
trap "rm -f $TMPFILE" EXIT

# ── Validate ──────────────────────────────────────────────────────────────────
log_section "Validate"

do_curl "POST /validate/" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/validate/" \
  -F "file=@$TMPFILE;filename=test.txt"
check "POST /api/v1/validate/"

do_curl "POST /validate/ max_size_mb=1" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/validate/?max_size_mb=1" \
  -F "file=@$TMPFILE;filename=test.txt"
check "POST /api/v1/validate/ (max_size_mb=1)"

# ── Extract ───────────────────────────────────────────────────────────────────
log_section "Extract"

do_curl "POST /extract/text" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/extract/text" \
  -F "file=@$TMPFILE;filename=test.txt"
check "POST /api/v1/extract/text"

do_curl "POST /extract/metadata" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/extract/metadata" \
  -F "file=@$TMPFILE;filename=test.txt"
check "POST /api/v1/extract/metadata"

# ── Preprocess ────────────────────────────────────────────────────────────────
log_section "Preprocess"

do_curl "POST /preprocess/text-clean" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/preprocess/text-clean" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This   is  a  test   with   extra   spaces  and  \"fancy quotes\".",
    "options": {
      "removeExtraSpaces": true,
      "normalizeQuotes": true,
      "fixEncoding": true,
      "removeHeaders": false,
      "removeFooters": false
    }
  }'
check "POST /api/v1/preprocess/text-clean"

do_curl "POST /preprocess/normalize" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/preprocess/normalize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document.\nIt has multiple lines.\nAnd some content.",
    "targetFormat": "plain"
  }'
check "POST /api/v1/preprocess/normalize"

do_curl "POST /preprocess/chunk" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/preprocess/chunk" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document for chunking. It contains enough text to be split into multiple chunks when a small chunk size is used. The chunking algorithm should respect word boundaries and create overlapping chunks as configured.",
    "chunkSize": 50,
    "overlap": 10
  }'
check "POST /api/v1/preprocess/chunk"

# ── Upload ────────────────────────────────────────────────────────────────────
log_section "Upload"

do_curl "POST /upload/" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/upload/" \
  -F "file=@$TMPFILE;filename=test.txt" \
  -F "project_id=test-project-001"
check "POST /api/v1/upload/"

FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)
if [ -z "$FILE_ID" ]; then
  log_warn "No fileId returned from upload — using fallback for ingest"
  FILE_ID="test-file-001"
else
  log_dbg "fileId: $FILE_ID"
fi

# ── Ingest ────────────────────────────────────────────────────────────────────
log_section "Ingest"

do_curl "POST /ingest/" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/ingest/" \
  -H "Content-Type: application/json" \
  -d "{
    \"fileId\": \"$FILE_ID\",
    \"projectId\": \"test-project-001\",
    \"options\": {
      \"cleanText\": true,
      \"extractMetadata\": true,
      \"chunkSize\": 1000,
      \"overlap\": 100
    }
  }"
check "POST /api/v1/ingest/"

JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)

if [ -n "$JOB_ID" ]; then
  log_dbg "Job ID: $JOB_ID"

  do_curl "GET /ingest/status/$JOB_ID" \
    "${AUTH_HEADER[@]}" \
    "$BASE/api/v1/ingest/status/$JOB_ID"
  if [ "$CODE" = "404" ]; then
    log_skip "GET /api/v1/ingest/status/$JOB_ID (404 — job already completed)"
    SKIP=$((SKIP + 2))  # skip status + cancel
  else
    check "GET /api/v1/ingest/status/$JOB_ID"

    do_curl "POST /ingest/cancel/$JOB_ID" \
      "${AUTH_HEADER[@]}" \
      -X POST "$BASE/api/v1/ingest/cancel/$JOB_ID"
    check "POST /api/v1/ingest/cancel/$JOB_ID"
  fi
else
  log_skip "No jobId returned — skipping status & cancel tests"
  SKIP=$((SKIP + 2))
fi

# ── Folders ───────────────────────────────────────────────────────────────────
log_section "Folders"

do_curl "POST /folders/" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/folders/"
check "POST /api/v1/folders/"

FOLDER_ID=$(echo "$BODY" | jq -r '.folderId // empty' 2>/dev/null)
if [ -n "$FOLDER_ID" ]; then
  log_ok "folderId generated: $FOLDER_ID" "-" "-"
  PASS=$((PASS + 1))
else
  log_fail "No folderId returned" "-" "-"
  FAIL=$((FAIL + 1))
fi
echo ""

# ── Ingest with folderId ──────────────────────────────────────────────────────
log_section "Ingest with folderId"

do_curl "POST /upload/ (for folder test)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/upload/" \
  -F "file=@$TMPFILE;filename=test-folder.txt" \
  -F "project_id=test-project-folder"
check "POST /api/v1/upload/ (folder)"

FOLDER_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)

if [ -n "$FOLDER_FILE_ID" ]; then
  do_curl "POST /ingest/ (with token)" \
    "${AUTH_HEADER[@]}" \
    -X POST "$BASE/api/v1/ingest/" \
    -H "Content-Type: application/json" \
    -d "{
      \"fileId\": \"$FOLDER_FILE_ID\",
      \"projectId\": \"test-project-folder\",
      \"options\": {\"cleanText\": true, \"extractMetadata\": true, \"chunkSize\": 1000, \"overlap\": 0}
    }"
  check "POST /api/v1/ingest/ (with token)"

  FOLDER_JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)
  if [ -n "$FOLDER_JOB_ID" ]; then
    sleep 2
    do_curl "GET /ingest/status/$FOLDER_JOB_ID (folderId check)" \
      "${AUTH_HEADER[@]}" \
      "$BASE/api/v1/ingest/status/$FOLDER_JOB_ID"
    check "GET /api/v1/ingest/status/$FOLDER_JOB_ID (folderId)"

    RETURNED_FOLDER_ID=$(echo "$BODY" | jq -r '.result.folderId // "null"' 2>/dev/null)
    log_ok "folderId from token: '$RETURNED_FOLDER_ID'" "-" "-"
    PASS=$((PASS + 1))
    echo ""
  fi
else
  log_skip "No fileId returned — skipping folderId test"
  SKIP=$((SKIP + 2))
fi

# ── Folders files ─────────────────────────────────────────────────────────────
log_section "Folders files"

if [ -n "$TOKEN" ]; then
  do_curl "GET /folders/files" \
    "${AUTH_HEADER[@]}" \
    "$BASE/api/v1/folders/files"
  check "GET /api/v1/folders/files"

  FILES_COUNT=$(echo "$BODY" | jq -r '.count // "null"' 2>/dev/null)
  FILES_FOLDER_ID=$(echo "$BODY" | jq -r '.folderId // "null"' 2>/dev/null)
  log_ok "folderId=$FILES_FOLDER_ID — $FILES_COUNT file(s) returned" "-" "-"
  echo "$BODY" | jq '.files[] | {fileId, fileName, fileType, projectId, folderId, processedAt}' 2>/dev/null | sed 's/^/    /'
  PASS=$((PASS + 1))
  echo ""
else
  log_skip "GET /api/v1/folders/files (no token)"
  SKIP=$((SKIP + 1))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary
