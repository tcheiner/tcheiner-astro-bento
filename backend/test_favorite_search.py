import sys
sys.path.append('.')
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Set the API key
os.environ['OPENAI_API_KEY'] = ''
question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

try:
    # Load FAISS index directly
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    print(f"=== TESTING: {question} ===")
    docs = vectorstore.similarity_search(question, k=5)
    
    print("Top 5 retrieved documents:")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        
        # Check what content we're getting
        source = doc.metadata.get('source', '').lower()
        content = doc.page_content.lower()
        
        if 'manaburn' in source:
            print("🎯 MANABURN CONTENT!")
            # Look specifically for the "favorite projects" text
            if 'favorite projects' in content:
                print("✅ Found 'favorite projects' text in ManaBurn!")
        elif 'crawler' in content or '2025-09-11' in source:
            print("🎯 WEB CRAWLER CONTENT!")
        elif 'astro' in source:
            print("⚠️  Astro website content (generic)")
            
        print(f"Content preview: {doc.page_content[:300]}...")
        print("---")
        
except Exception as e:
    print(f"Error: {e}")