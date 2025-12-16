#!/bin/bash

# Test the local server endpoint
# Run this in a separate terminal after starting test_local.sh

echo "=========================================="
echo "Testing Local Image Storage Endpoint"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "❌ Error: Server is not running on http://localhost:8080"
    echo ""
    echo "Please start the server first:"
    echo "  ./test_local.sh"
    exit 1
fi

echo "✓ Server is running"
echo ""
echo "Sending POST request to process images..."
echo ""

# Make the request and format the JSON response
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  | python3 -m json.tool 2>/dev/null || cat

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
