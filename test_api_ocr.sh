#!/bin/bash
# Usage:
#   ./test_api_ocr.sh [host]                  # https://host (default: visiobook.cloud)
#   PROTOCOL=http ./test_api_ocr.sh localhost:8090
#   DEBUG=1 ./test_api_ocr.sh                 # verbose curl output

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

# ── Create test image (PNG with text via Python) ───────────────────────────────
IMG_FILE=$(mktemp /tmp/test-ocr-XXXX.png)
python3 - "$IMG_FILE" <<'PYEOF'
import sys
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 35), "OCR Test Document - Hello World 1234", fill=(0, 0, 0))
    img.save(sys.argv[1])
except Exception as e:
    print(f"Could not create test image: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

if [ $? -ne 0 ] || [ ! -s "$IMG_FILE" ]; then
  log_warn "PIL not available or image creation failed — skipping OCR image tests"
  SKIP=$((SKIP + 3))
  IMG_FILE=""
fi

# ── Create minimal test PDF ────────────────────────────────────────────────────
PDF_FILE=$(mktemp /tmp/test-ocr-XXXX.pdf)
python3 - "$PDF_FILE" <<'PYEOF'
import sys
content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>
stream
BT /F1 12 Tf 100 700 Td (OCR PDF Test Document) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""
with open(sys.argv[1], 'wb') as f:
    f.write(content)
PYEOF

trap "rm -f $IMG_FILE $PDF_FILE" EXIT

# ── OCR Image Upload + Ingest ─────────────────────────────────────────────────
if [ -n "$IMG_FILE" ]; then
  log_section "OCR — Image (PNG)"

  do_curl "POST /upload/ (PNG)" \
    "${AUTH_HEADER[@]}" \
    -X POST "$BASE/api/v1/upload/" \
    -F "file=@$IMG_FILE;filename=test-ocr.png" \
    -F "project_id=test-ocr-project"
  check "POST /api/v1/upload/ (PNG)"

  IMG_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)

  if [ -n "$IMG_FILE_ID" ]; then
    do_curl "POST /ingest/ (PNG)" \
      "${AUTH_HEADER[@]}" \
      -X POST "$BASE/api/v1/ingest/" \
      -H "Content-Type: application/json" \
      -d "{
        \"fileId\": \"$IMG_FILE_ID\",
        \"projectId\": \"test-ocr-project\",
        \"options\": {\"cleanText\": true, \"extractMetadata\": true, \"chunkSize\": 1000, \"overlap\": 0}
      }"
    check "POST /api/v1/ingest/ (PNG)"

    JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)
    if [ -n "$JOB_ID" ]; then
      FINAL_STATUS=$(poll_job "$JOB_ID")
      do_curl "GET /ingest/status/$JOB_ID (PNG final)" \
        "${AUTH_HEADER[@]}" \
        "$BASE/api/v1/ingest/status/$JOB_ID"
      if [ "$FINAL_STATUS" = "completed" ]; then
        log_ok "OCR ingest PNG — job completed" "$CODE" "$ELAPSED"
        echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
        PASS=$((PASS + 1))
      else
        log_fail "OCR ingest PNG — job $FINAL_STATUS" "$CODE" "$ELAPSED"
        echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
        FAIL=$((FAIL + 1))
      fi
      echo ""
    fi
  fi
fi

# ── PDF Upload + Ingest ───────────────────────────────────────────────────────
log_section "OCR — PDF"

do_curl "POST /upload/ (PDF)" \
  "${AUTH_HEADER[@]}" \
  -X POST "$BASE/api/v1/upload/" \
  -F "file=@$PDF_FILE;filename=test-ocr.pdf" \
  -F "project_id=test-ocr-project"
check "POST /api/v1/upload/ (PDF)"

PDF_FILE_ID=$(echo "$BODY" | jq -r '.fileId // empty' 2>/dev/null)

if [ -n "$PDF_FILE_ID" ]; then
  do_curl "POST /ingest/ (PDF)" \
    "${AUTH_HEADER[@]}" \
    -X POST "$BASE/api/v1/ingest/" \
    -H "Content-Type: application/json" \
    -d "{
      \"fileId\": \"$PDF_FILE_ID\",
      \"projectId\": \"test-ocr-project\",
      \"options\": {\"cleanText\": true, \"extractMetadata\": true, \"chunkSize\": 1000, \"overlap\": 0}
    }"
  check "POST /api/v1/ingest/ (PDF)"

  JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty' 2>/dev/null)
  if [ -n "$JOB_ID" ]; then
    FINAL_STATUS=$(poll_job "$JOB_ID")
    do_curl "GET /ingest/status/$JOB_ID (PDF final)" \
      "${AUTH_HEADER[@]}" \
      "$BASE/api/v1/ingest/status/$JOB_ID"
    if [ "$FINAL_STATUS" = "completed" ]; then
      log_ok "OCR ingest PDF — job completed" "$CODE" "$ELAPSED"
      echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
      PASS=$((PASS + 1))
    else
      log_fail "OCR ingest PDF — job $FINAL_STATUS" "$CODE" "$ELAPSED"
      echo "$BODY" | jq . 2>/dev/null | sed 's/^/    /'
      FAIL=$((FAIL + 1))
    fi
    echo ""
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary
