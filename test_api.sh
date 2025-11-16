#!/bin/bash
# Test script for OpenImage API

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "Testing OpenImage API"
echo "API URL: $API_URL"
echo "=========================================="

# Test 1: Health check
echo -e "\n1. Testing health endpoint..."
curl -s "$API_URL/health" | python3 -m json.tool

# Test 2: Status
echo -e "\n\n2. Testing status endpoint..."
curl -s "$API_URL/api/status" | python3 -m json.tool

# Test 3: Sources
echo -e "\n\n3. Testing sources endpoint..."
curl -s "$API_URL/api/sources" | python3 -m json.tool

# Test 4: Search for a thing (no face detection)
echo -e "\n\n4. Testing search for 'Eiffel Tower' (thing)..."
curl -s -X POST "$API_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Eiffel Tower",
    "entity_type": "thing",
    "max_results": 5,
    "require_face": false
  }' | python3 -m json.tool | head -50

# Test 5: Search for a person
echo -e "\n\n5. Testing search for 'Emmanuel Macron' (person)..."
curl -s -X POST "$API_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Emmanuel Macron",
    "entity_type": "person",
    "max_results": 3,
    "require_face": true
  }' | python3 -m json.tool | head -80

# Test 6: Invalid request (missing query)
echo -e "\n\n6. Testing error handling (missing query)..."
curl -s -X POST "$API_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person"
  }' | python3 -m json.tool

# Test 7: Invalid entity type
echo -e "\n\n7. Testing error handling (invalid entity type)..."
curl -s -X POST "$API_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "entity_type": "invalid"
  }' | python3 -m json.tool

echo -e "\n\n=========================================="
echo "All tests completed!"
echo "=========================================="
