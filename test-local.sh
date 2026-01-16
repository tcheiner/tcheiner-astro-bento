  #!/bin/bash
  echo "Testing local backend..."

  echo -e "\n1. Health check:"
  curl -s http://localhost:8000/health | jq

  echo -e "\n2. Root endpoint:"
  curl -s http://localhost:8000/ | jq

  echo -e "\n3. Chatbot response:"
  curl -s -X POST "http://localhost:8000/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "Tell me about your leadership experience"}' \
    | jq '.answer' -r | head -20

  echo -e "\n\nDone! Full stack running on:"
  echo "  Backend:  http://localhost:8000"
  echo "  Frontend: http://localhost:4321"

