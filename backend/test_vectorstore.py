import sys
sys.path.append('.')
from chatbot.services import query_vectorstore
import json

question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

print(f"Testing question: {question}")
print()

try:
    # Test vectorstore retrieval without OpenAI
    from chatbot.main import get_vectorstore
    vectorstore = get_vectorstore()
    
    # Search for relevant documents
    docs = vectorstore.similarity_search(question, k=5)
    
    print("Retrieved documents:")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content preview: {doc.page_content[:200]}...")
        
except Exception as e:
    print(f"Error: {e}")