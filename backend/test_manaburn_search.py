import sys
sys.path.append('.')
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Set the API key
os.environ['OPENAI_API_KEY'] = ''
try:
    # Load FAISS index directly
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Search specifically for ManaBurn content
    print("=== SEARCHING FOR MANABURN ===")
    docs = vectorstore.similarity_search("ManaBurn AI game platform technical challenges", k=3)
    
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        if 'manaburn' in doc.metadata.get('source', '').lower():
            print("*** FOUND MANABURN CONTENT ***")
        print(f"Content preview: {doc.page_content[:400]}...")
        print("---")
    
    print("\n=== SEARCHING FOR WEB CRAWLER ===")
    docs = vectorstore.similarity_search("web crawler Reddit analytics trending keywords", k=3)
    
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        if 'crawler' in doc.page_content.lower() or 'reddit' in doc.page_content.lower():
            print("*** FOUND CRAWLER CONTENT ***")
        print(f"Content preview: {doc.page_content[:400]}...")
        print("---")
        
except Exception as e:
    print(f"Error: {e}")
