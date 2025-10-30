#!/usr/bin/env python3
"""
Debug why ManaBurn isn't appearing in custom scoring results
"""

import sys
sys.path.append('.')
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()
os.environ['OPENAI_API_KEY'] = '***REMOVED***'

question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

def debug_manaburn_scoring():
    print("🔍 DEBUGGING MANABURN CUSTOM SCORING")
    print("=" * 60)
    
    try:
        # Load vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        print(f"📊 Total documents in vectorstore: {vectorstore.index.ntotal}")
        
        # 1. First check if ManaBurn content exists at all
        print(f"\n1️⃣ SEARCHING FOR MANABURN CONTENT DIRECTLY...")
        manaburn_docs = vectorstore.similarity_search("ManaBurn favorite project", k=10)
        
        manaburn_found = False
        for i, doc in enumerate(manaburn_docs):
            source = doc.metadata.get('source', '').lower()
            if 'manaburn' in source:
                print(f"✅ Found ManaBurn content!")
                print(f"   📁 Source: {doc.metadata.get('source')}")
                print(f"   📝 Content: {doc.page_content[:200]}...")
                manaburn_found = True
                break
        
        if not manaburn_found:
            print("❌ NO MANABURN CONTENT FOUND IN VECTORSTORE!")
            print("   This means the content wasn't indexed properly")
            return False
        
        # 2. Test regular similarity search with the actual question
        print(f"\n2️⃣ REGULAR SIMILARITY SEARCH (no custom scoring)...")
        regular_docs = vectorstore.similarity_search(question, k=15)
        
        print("Top 15 results from regular similarity search:")
        manaburn_position = None
        for i, doc in enumerate(regular_docs):
            source = doc.metadata.get('source', '').lower()
            print(f"   {i+1:2d}. {doc.metadata.get('source', 'Unknown')}")
            if 'manaburn' in source:
                manaburn_position = i + 1
                print(f"       🎯 MANABURN FOUND AT POSITION {manaburn_position}!")
        
        if manaburn_position is None:
            print(f"❌ ManaBurn not in top 15 regular similarity results!")
            print(f"   This means it's semantically distant from the question")
        else:
            print(f"✅ ManaBurn found at position {manaburn_position} in regular search")
        
        # 3. Test custom scoring manually
        print(f"\n3️⃣ TESTING CUSTOM SCORING BOOSTS...")
        
        from chatbot.services import CustomScoringRetriever
        try:
            custom_retriever = CustomScoringRetriever(vectorstore=vectorstore, k=8)
            print(f"✅ CustomScoringRetriever created successfully")
            
            # Get docs with custom scoring
            custom_docs = custom_retriever.get_relevant_documents(question)
            
            print(f"Custom scoring results:")
            for i, doc in enumerate(custom_docs):
                source = doc.metadata.get('source', '')
                print(f"   {i+1}. {source}")
                
                if 'manaburn' in source.lower():
                    print(f"       🎯 MANABURN FOUND AT POSITION {i+1}!")
                    print(f"       📊 Scoring details:")
                    print(f"          Original Score: {doc.metadata.get('original_score', 'N/A'):.4f}")
                    print(f"          Boosted Score:  {doc.metadata.get('boosted_score', 'N/A'):.4f}")
                    print(f"          Total Boost:    {doc.metadata.get('total_boost', 0):.4f}")
                    print(f"          Recency Boost:  {doc.metadata.get('recency_boost', 0):.4f}")
                    print(f"          Keyword Boost:  {doc.metadata.get('keyword_boost', 0):.4f}")
                    return True
            
            print(f"❌ ManaBurn still not in top {len(custom_docs)} custom scoring results!")
            
        except Exception as e:
            print(f"❌ Error testing CustomScoringRetriever: {e}")
            return False
        
        # 4. Test boost calculation manually
        print(f"\n4️⃣ MANUAL BOOST CALCULATION TEST...")
        
        # Find a ManaBurn doc and test boost calculation
        for doc in manaburn_docs:
            if 'manaburn' in doc.metadata.get('source', '').lower():
                print(f"Testing boost calculation on ManaBurn doc...")
                
                content = doc.page_content.lower()
                metadata = doc.metadata
                
                # Test keyword matching
                from chatbot.services import SCORING_KEYWORDS
                
                pride_matches = sum(1 for word in SCORING_KEYWORDS.get('pride_terms', []) if word in content)
                mgmt_matches = sum(1 for word in SCORING_KEYWORDS.get('management_skills', []) if word in content)
                tech_matches = sum(1 for word in SCORING_KEYWORDS.get('technical_skills', []) if word in content)
                
                print(f"   Pride term matches: {pride_matches}")
                print(f"   Management matches: {mgmt_matches}")  
                print(f"   Technical matches: {tech_matches}")
                
                # Check if 'favorite' tag is there
                tags = metadata.get('tags', [])
                print(f"   Tags: {tags}")
                
                if 'favorite' in tags or 'favorite' in content:
                    print(f"   ✅ Contains 'favorite' - should get boost!")
                else:
                    print(f"   ⚠️  No 'favorite' found")
                
                break
        
        return False
        
    except Exception as e:
        print(f"❌ Error in debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_manaburn_scoring()
    
    if not success:
        print(f"\n💡 POSSIBLE SOLUTIONS:")
        print(f"   1. Increase boost values in .env (try 0.5-1.0)")
        print(f"   2. Add more 'favorite' keywords to ManaBurn content")
        print(f"   3. Rebuild vectorstore if content changed")
        print(f"   4. Check that 'favorite' is in ManaBurn tags")