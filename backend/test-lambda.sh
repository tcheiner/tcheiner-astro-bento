 #!/bin/bash
  API_URL="https://5f3ysv93x1.execute-api.us-east-1.amazonaws.com/prod"

  echo "Testing health..."
  curl -s "$API_URL/health" | jq

  echo -e "\n\nTesting chatbot..."
  curl -s -X POST "$API_URL/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "Tell me about your leadership experience"}' | jq '.answer' -r

  echo -e "\n\nDone!"
