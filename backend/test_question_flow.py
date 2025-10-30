import sys
sys.path.append('.')
import os
from chatbot.filters import is_question_about_tc

# Test the content filtering
question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

print(f"Testing question: {question}")
print()

# Test content filtering
is_relevant = is_question_about_tc(question)
print(f"Content filter result: {is_relevant}")

if not is_relevant:
    print("❌ ISSUE: Question is being blocked by content filter!")
else:
    print("✅ Question passes content filter")
    
    # Test similarity search with the exact question
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    
    os.environ['OPENAI_API_KEY'] = ''
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    print(f"\n=== SIMILARITY SEARCH FOR EXACT QUESTION ===")
    docs = vectorstore.similarity_search(question, k=5)
    
    print("Top 5 retrieved documents:")
    for i, doc in enumerate(docs):
        print(f"\nDoc {i+1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        
        # Check if it's ManaBurn or web crawler content
        source = doc.metadata.get('source', '').lower()
        content = doc.page_content.lower()
        
        if 'manaburn' in source:
            print("🎯 MANABURN CONTENT FOUND!")
        elif '2025-09-11' in source or 'crawler' in content:
            print("🎯 WEB CRAWLER CONTENT FOUND!")
        elif 'favorite' in content and 'platform migration' in content:
            print("🎯 WELLS FARGO FAVORITE PROJECT FOUND!")
            
        print(f"Content preview: {doc.page_content[:200]}...")
        print("---")
