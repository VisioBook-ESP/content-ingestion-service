#!/bin/bash
# Auto-format code with black and ruff

set -e

echo "Formatting code with black..."
black src tests

echo "Fixing imports with ruff..."
ruff check --fix src tests || true

echo "Done! Please review changes and commit."
