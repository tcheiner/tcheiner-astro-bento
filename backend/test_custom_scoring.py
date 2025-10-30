#!/usr/bin/env python3
"""
Test the custom scoring retrieval system locally
Shows detailed scoring breakdown for debugging
"""

import sys
sys.path.append('.')
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the API key
os.environ['OPENAI_API_KEY'] = '***REMOVED***'

question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

def test_custom_scoring_detailed():
    print(f"🎯 Testing Custom Scoring Strategy")
    print(f"Question: {question}")
    print("=" * 80)
    
    try:
        # Load vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        # Test the custom retriever directly
        from chatbot.services import CustomScoringRetriever, RETRIEVAL_K
        retriever = CustomScoringRetriever(vectorstore=vectorstore, k=RETRIEVAL_K)
        
        print(f"📊 Using CustomScoringRetriever with k={RETRIEVAL_K}")
        print()
        
        # Get documents with detailed scoring info
        docs = retriever.get_relevant_documents(question)
        
        print(f"📋 Retrieved {len(docs)} documents with custom scoring:")
        print()
        
        for i, doc in enumerate(docs):
            print(f"🔍 Doc {i+1}:")
            print(f"   📁 Source: {doc.metadata.get('source', 'Unknown')}")
            
            # Show scoring breakdown
            if 'total_boost' in doc.metadata:
                print(f"   📊 Scoring Breakdown:")
                print(f"      • Original Score: {doc.metadata.get('original_score', 'N/A'):.4f}")
                print(f"      • Boosted Score:  {doc.metadata.get('boosted_score', 'N/A'):.4f}")
                print(f"      • Total Boost:    {doc.metadata.get('total_boost', 0):.4f}")
                print(f"      • Recency Boost:  {doc.metadata.get('recency_boost', 0):.4f}")
                print(f"      • Keyword Boost:  {doc.metadata.get('keyword_boost', 0):.4f}")
                print(f"      • Years Found:    {doc.metadata.get('years_found', [])}")
            
            # Check what content we're getting
            source = doc.metadata.get('source', '').lower()
            content = doc.page_content.lower()
            
            if 'manaburn' in source:
                print(f"   🎯 MANABURN CONTENT! ⭐")
                if 'favorite' in content or 'proud' in content:
                    print(f"      ✅ Contains pride/favorite terms")
            elif 'crawler' in content or '2025-09-11' in source:
                print(f"   🎯 WEB CRAWLER CONTENT! ⭐")
            elif 'wellsfargo' in source and 'favorite' in content:
                print(f"   🎯 WELLS FARGO FAVORITE PROJECT")
            elif 'astro' in source:
                print(f"   ⚠️  Astro website (less specific)")
            else:
                print(f"   📄 Other content")
                
            print(f"   📝 Content preview: {doc.page_content[:150]}...")
            print("-" * 60)
        
        # Test the full pipeline with GPT
        print(f"\n🤖 Testing Full GPT Pipeline:")
        print("=" * 50)
        
        from chatbot.services import get_qa_chain
        qa_chain = get_qa_chain(vectorstore)
        
        result = qa_chain.invoke({"query": question})
        print("🎯 GPT Response:")
        print(result["result"])
        print()
        
        print("📚 Sources used:")
        for i, source_doc in enumerate(result["source_documents"]):
            print(f"   {i+1}. {source_doc.metadata.get('source', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing custom scoring: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_config():
    """Test that environment variables are loaded correctly"""
    print(f"\n🔧 Environment Configuration:")
    print("=" * 40)
    
    from chatbot.services import (
        RETRIEVAL_STRATEGY, RETRIEVAL_K, RECENCY_BOOST, 
        IMPRESSIVE_KEYWORDS_BOOST, TECHNICAL_TERMS_BOOST, PRIDE_TERMS_BOOST
    )
    
    print(f"RETRIEVAL_STRATEGY: {RETRIEVAL_STRATEGY}")
    print(f"RETRIEVAL_K: {RETRIEVAL_K}")
    print(f"RECENCY_BOOST: {RECENCY_BOOST}")
    print(f"IMPRESSIVE_KEYWORDS_BOOST: {IMPRESSIVE_KEYWORDS_BOOST}")
    print(f"TECHNICAL_TERMS_BOOST: {TECHNICAL_TERMS_BOOST}")
    print(f"PRIDE_TERMS_BOOST: {PRIDE_TERMS_BOOST}")
    
    # Test keyword loading
    from chatbot.services import SCORING_KEYWORDS
    print(f"\nKeyword Categories Loaded: {len(SCORING_KEYWORDS)}")
    for category in SCORING_KEYWORDS:
        print(f"  • {category}: {len(SCORING_KEYWORDS[category])} terms")
    
    print(f"\nTechnical skills sample: {', '.join(SCORING_KEYWORDS.get('technical_skills', [])[:10])}")

if __name__ == "__main__":
    print("🚀 Testing Custom Scoring System")
    print("=" * 50)
    
    # Test environment
    test_environment_config()
    
    # Test custom scoring
    success = test_custom_scoring_detailed()
    
    if success:
        print(f"\n🎉 Custom scoring test completed successfully!")
        print(f"💡 Look for ManaBurn and Web Crawler content in the results above")
    else:
        print(f"\n❌ Custom scoring test failed")
        
    print(f"\n📝 Next steps:")
    print(f"   1. If ManaBurn/Web Crawler appear in top results: SUCCESS! ✅")
    print(f"   2. If not, try adjusting boost values in .env file")
    print(f"   3. Deploy with: ./build-container.sh")