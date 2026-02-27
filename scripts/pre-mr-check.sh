#!/usr/bin/env bash
# pre-mr-check.sh — Run all checks before opening a merge request.
# Usage: bash scripts/pre-mr-check.sh
# Exit code: 0 if all checks pass, 1 otherwise.

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ──────────────────────────────────────────────────────────────────
FAILED_STEPS=()

header() {
    echo ""
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════${RESET}"
    echo -e "${CYAN}${BOLD}  $1${RESET}"
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════${RESET}"
}

run_step() {
    local name="$1"
    shift
    echo -e "\n${YELLOW}▶ $name${RESET}"
    if "$@"; then
        echo -e "${GREEN}✔ $name passed${RESET}"
    else
        echo -e "${RED}✘ $name failed${RESET}"
        FAILED_STEPS+=("$name")
    fi
}

# ── Checks ───────────────────────────────────────────────────────────────────
header "Pre-MR checks — content-ingestion-service"

# 1. Format: black (check only, no modification)
run_step "black (format check)" \
    black src tests --check --diff

# 2. Format: isort (check only)
run_step "isort (import order check)" \
    isort src tests --check-only --diff

# 3. Linting: flake8
run_step "flake8 (lint)" \
    flake8 src tests

# 4. Type checking: mypy
run_step "mypy (type check)" \
    mypy src

# 5. Tests with coverage
run_step "pytest (tests + coverage)" \
    pytest --cov=src --cov-report=term-missing --cov-report=xml -q

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════${RESET}"

if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}${BOLD}  All checks passed — ready to open a MR!${RESET}"
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════${RESET}"
    exit 0
else
    echo -e "${RED}${BOLD}  ${#FAILED_STEPS[@]} check(s) failed:${RESET}"
    for step in "${FAILED_STEPS[@]}"; do
        echo -e "${RED}    • $step${RESET}"
    done
    echo -e "${CYAN}${BOLD}══════════════════════════════════════════${RESET}"
    exit 1
fi
