#!/bin/bash

IP=visiobook.cloud
BASE=https://$IP
PASS=0
FAIL=0
RAND=$(head -c 4 /dev/urandom | xxd -p)
EMAIL="test-${RAND}@example.com"
USERNAME="user-${RAND}"
DEBUG=${DEBUG:-0}

dbg() { [ "$DEBUG" = "1" ] && echo "  [DBG] $*"; }

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
    return 1 2>/dev/null || exit 1
  fi
  echo ""
}

echo "=== Routes publiques ==="
echo ""

echo "--- Register ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST $BASE/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"'"$EMAIL"'","password":"SecurePassword123!","username":"'"$USERNAME"'"}')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "POST /api/v1/auth/register" "$BODY" "$CODE"

echo "--- Login ---"
RESP=$(curl -s -w "\n%{http_code}" -X POST $BASE/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"$EMAIL"'","password":"SecurePassword123!"}')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
TOKEN=$(echo "$BODY" | jq -r '.access_token')
check "POST /api/v1/auth/login" "$BODY" "$CODE"

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "  [FAIL] No token received, cannot continue"
  exit 1
fi
echo "Token: ${TOKEN:0:50}..."
echo "$TOKEN" > /tmp/esp_test_token
echo ""

echo "=== Routes user (JWT) ==="
echo ""

echo "--- GET /users/me ---"
RESP=$(curl -s -w "\n%{http_code}" $BASE/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN")
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "GET /api/v1/users/me" "$BODY" "$CODE"

echo "--- PUT /users/me ---"
RESP=$(curl -s -w "\n%{http_code}" -X PUT $BASE/api/v1/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"first_name":"John","last_name":"Doe"}')
BODY=$(echo "$RESP" | sed '$d')
CODE=$(echo "$RESP" | tail -1)
check "PUT /api/v1/users/me" "$BODY" "$CODE"

echo "=== Result: $PASS passed, $FAIL failed ==="