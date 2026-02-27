#!/bin/bash
IP=${1:-${API_HOST:-visiobook.cloud}}
BASE=https://$IP
PASS=0
FAIL=0
DEBUG=${DEBUG:-0}
CURL_OPTS="--connect-timeout 5 --max-time 10 -s"

dbg() { [ "$DEBUG" = "1" ] && echo "  [DBG] $*"; }

# Récupère le token généré par test_api_user_core.sh
if [ -f /tmp/esp_test_token ]; then
  TOKEN=$(cat /tmp/esp_test_token)
  echo "Token loaded: ${TOKEN:0:50}..."
  echo ""
else
  echo "  [WARN] No token found — run bash test_api_user_core.sh first if auth is needed"
  TOKEN=""
fi

# Create a temp test file for upload tests
TMPFILE=$(mktemp /tmp/test-XXXX.txt)
echo "This is a test document for content ingestion. It contains some sample text to validate extraction and preprocessing features." > "$TMPFILE"

cleanup() {
  rm -f "$TMPFILE"
}
trap cleanup EXIT

check() {
  local name="$1"
  local response="$2"
  local http_code="$3"
  local method path
  method=$(echo "$name" | cut -d' ' -f1)
  path=$(echo "$name" | cut -d' ' -f2-)

  dbg "→ $method $BASE$path"
  dbg "← HTTP $http_code"

  if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
    echo "  [OK] $name (HTTP $http_code)"
    echo "$response" | jq . 2>/dev/null
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] $name (HTTP $http_code)"
    if [ "$http_code" = "000" ]; then
      dbg "Cannot connect to $BASE — is the service running?"
    fi
    echo "$response"
    FAIL=$((FAIL + 1))
    echo ""
    echo "--- Test stopped: $name failed ---"
    echo "Result: $PASS passed, $FAIL failed"
    exit 1
  fi
  echo ""
}

# ─────────────────────────────────────────────
echo "=== Validate ==="
echo ""

echo "--- POST /validate/ ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/validate/" \
  -F "file=@$TMPFILE;filename=test.txt")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/validate/" "$BODY" "$CODE"

echo "--- POST /validate/ (max_size_mb=1) ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/validate/?max_size_mb=1" \
  -F "file=@$TMPFILE;filename=test.txt")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/validate/ (max_size_mb=1)" "$BODY" "$CODE"

# ─────────────────────────────────────────────
echo "=== Extract ==="
echo ""

echo "--- POST /extract/text ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/extract/text" \
  -F "file=@$TMPFILE;filename=test.txt")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/extract/text" "$BODY" "$CODE"

echo "--- POST /extract/metadata ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/extract/metadata" \
  -F "file=@$TMPFILE;filename=test.txt")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/extract/metadata" "$BODY" "$CODE"

# ─────────────────────────────────────────────
echo "=== Preprocess ==="
echo ""

echo "--- POST /preprocess/text-clean ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/preprocess/text-clean" \
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
  }')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/preprocess/text-clean" "$BODY" "$CODE"

echo "--- POST /preprocess/normalize ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/preprocess/normalize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document.\nIt has multiple lines.\nAnd some content.",
    "targetFormat": "plain"
  }')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/preprocess/normalize" "$BODY" "$CODE"

echo "--- POST /preprocess/chunk ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/preprocess/chunk" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document for chunking. It contains enough text to be split into multiple chunks when a small chunk size is used. The chunking algorithm should respect word boundaries and create overlapping chunks as configured.",
    "chunkSize": 50,
    "overlap": 10
  }')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/preprocess/chunk" "$BODY" "$CODE"

# ─────────────────────────────────────────────
echo "=== Ingest ==="
echo ""

echo "--- POST /ingest/ ---"
RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/ingest/" \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "test-file-001",
    "projectId": "test-project-001",
    "options": {
      "cleanText": true,
      "extractMetadata": true,
      "chunkSize": 1000,
      "overlap": 100
    }
  }')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/ingest/" "$BODY" "$CODE"

JOB_ID=$(echo "$BODY" | jq -r '.jobId // empty')

if [ -n "$JOB_ID" ]; then
  echo "Job ID: $JOB_ID"
  echo ""

  echo "--- GET /ingest/status/{job_id} ---"
  RESP=$(curl $CURL_OPTS -w "\n%{http_code}" "$BASE/api/v1/ingest/status/$JOB_ID")
  BODY=$(echo "$RESP" | sed '$d')
  CODE=$(echo "$RESP" | tail -1)
  check "GET /api/v1/ingest/status/$JOB_ID" "$BODY" "$CODE"

  echo "--- POST /ingest/cancel/{job_id} ---"
  RESP=$(curl $CURL_OPTS -w "\n%{http_code}" -X POST "$BASE/api/v1/ingest/cancel/$JOB_ID")
  BODY=$(echo "$RESP" | sed '$d')
  CODE=$(echo "$RESP" | tail -1)
  check "POST /api/v1/ingest/cancel/$JOB_ID" "$BODY" "$CODE"
else
  echo "  [SKIP] No jobId returned, skipping status and cancel tests"
  echo ""
fi

# ─────────────────────────────────────────────
echo "=== Result: $PASS passed, $FAIL failed ==="
