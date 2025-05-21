#!/bin/bash

# Health Check
echo "=== Test 1: API Health Check ==="
HEALTH_RESP=$(curl -s http://localhost:8000)
if [[ "$HEALTH_RESP" == *"Login"* ]]; then
  echo "Passed"
else
  echo "Failed"
  echo "Response: $HEALTH_RESP"
  exit 1
fi
