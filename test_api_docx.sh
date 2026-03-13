#!/bin/bash
# Usage:
#   ./test_api_docx.sh [host]                  # https://host (default: visiobook.cloud)
#   PROTOCOL=http ./test_api_docx.sh localhost:8090
#   DEBUG=1 ./test_api_docx.sh                 # verbose curl output

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

# ── Create test DOCX file (minimal OOXML via zipfile — no dependencies) ────────
DOCX_FILE=$(mktemp /tmp/test-docx-XXXX.docx)
python3 - "$DOCX_FILE" <<'PYEOF'
import sys, zipfile

CONTENT_TYPES = '<?xml version="1.0" encoding="UTF-8"?>\
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\
<Default Extension="xml" ContentType="application/xml"/>\
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\
</Types>'

RELS = '<?xml version="1.0" encoding="UTF-8"?>\
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\
</Relationships>'

DOCUMENT = '<?xml version="1.0" encoding="UTF-8"?>\
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\
<w:body>\
<w:p><w:r><w:t>DOCX Test Document</w:t></w:r></w:p>\
<w:p><w:r><w:t>This is a test paragraph for DOCX ingestion.</w:t></w:r></w:p>\
<w:p><w:r><w:t>It contains multiple sentences to verify text extraction.</w:t></w:r></w:p>\
<w:p><w:r><w:t>Second section content for chunking validation.</w:t></w:r></w:p>\
</w:body>\
</w:document>'

WORD_RELS = '<?xml version="1.0" encoding="UTF-8"?>\
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\
</Relationships>'

try:
    with zipfile.ZipFile(sys.argv[1], 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES)
        z.writestr('_rels/.rels', RELS)
        z.writestr('word/document.xml', DOCUMENT)
        z.writestr('word/_rels/document.xml.rels', WORD_RELS)
except Exception as e:
    print(f"Could not create test DOCX: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

if [ $? -ne 0 ] || [ ! -s "$DOCX_FILE" ]; then
  log_warn "DOCX creation failed — skipping"
  SKIP=$((SKIP + 2))
  print_summary
  exit 0
fi

trap "rm -f $DOCX_FILE" EXIT

# ── DOCX Upload + Ingest ───────────────────────────────────────────────────────
log_section "DOCX — Upload & Ingest"

do_curl "POST /upload/ (DOCX)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/upload/" \
  -F "file=@$DOCX_FILE;filename=test-doc.docx" \
  -F "project_id=test-docx-project"
check "POST /api/v1/upload/ (DOCX)"

DOCX_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)

if [ -z "$DOCX_FILE_ID" ]; then
  log_warn "No fileId returned — skipping ingest"
  SKIP=$((SKIP + 1))
  print_summary
  exit 0
fi

do_curl "POST /ingest/ (DOCX)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/ingest/" \
  -H "Content-Type: application/json" \
  -d "{
    \"fileId\": \"$DOCX_FILE_ID\",
    \"projectId\": \"test-docx-project\",
    \"options\": {\"cleanText\": true, \"extractMetadata\": true, \"chunkSize\": 1000, \"overlap\": 0}
  }"
check "POST /api/v1/ingest/ (DOCX)"

JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)
if [ -n "$JOB_ID" ]; then
  FINAL_STATUS=$(poll_job "$JOB_ID")
  do_curl "GET /ingest/status/$JOB_ID (DOCX final)" \
    "${AUTH_HEADER[@]}" \
    "$BASE/api/v1/ingest/status/$JOB_ID"
  if [ "$FINAL_STATUS" = "completed" ]; then
    log_ok "DOCX ingest — job completed" "$CODE" "$ELAPSED"
    echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    PASS=$((PASS + 1))
  else
    log_fail "DOCX ingest — job $FINAL_STATUS" "$CODE" "$ELAPSED"
    echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
    FAIL=$((FAIL + 1))
  fi
  echo ""
fi

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary
