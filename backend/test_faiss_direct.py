import sys
sys.path.append('.')
import pickle
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Set the API key
os.environ['OPENAI_API_KEY'] = ''
question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

print(f"Testing question: {question}")
print()

try:
    # Load FAISS index directly
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Search for relevant documents
    docs = vectorstore.similarity_search(question, k=5)
    
    print("Retrieved documents:")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content preview: {doc.page_content[:300]}...")
        print("---")
        
except Exception as e:
    print(f"Error: {e}")
