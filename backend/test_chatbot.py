import sys
sys.path.append('.')
from chatbot.main import ask_endpoint
from chatbot.models import AskRequest
import json

question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'
request = AskRequest(question=question)
response = ask_endpoint(request)

# Extract JSON from Response object
response_data = json.loads(response.body.decode('utf-8'))
print('Response:')
print(json.dumps(response_data, indent=2))