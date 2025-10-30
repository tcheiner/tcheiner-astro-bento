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
os.environ['OPENAI_API_KEY'] = ''
question = 'Tell us about your favorite thing you built. Share the technical challenges, your approach, and why you are proud of it.'

def test_strategy(strategy_name, retriever_config):
    print(f"\n{'='*60}")
    print(f"TESTING STRATEGY: {strategy_name}")
    print(f"Config: {retriever_config}")
    print(f"{'='*60}")
    
    try:
        # Load vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings, allow_dangerous_deserialization=True)
        
        # Create retriever with specific config
        if retriever_config['search_type'] == 'mmr':
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": retriever_config['k'],
                    "fetch_k": retriever_config.get('fetch_k', 20),
                    "lambda_mult": retriever_config.get('lambda_mult', 0.7)
                }
            )
        else:
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": retriever_config['k'],
                    "score_threshold": retriever_config.get('score_threshold', 0.5)
                }
            )
        
        # Get documents
        docs = retriever.get_relevant_documents(question)
        
        print(f"\nRetrieved {len(docs)} documents:")
        for i, doc in enumerate(docs):
            print(f"\nDoc {i+1}:")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            
            # Check what content we're getting
            source = doc.metadata.get('source', '').lower()
            content = doc.page_content.lower()
            
            if 'manaburn' in source:
                print("🎯 MANABURN CONTENT!")
                if 'favorite projects' in content:
                    print("   ✅ Contains 'favorite projects' text")
            elif 'crawler' in content or '2025-09-11' in source:
                print("🎯 WEB CRAWLER CONTENT!")
            elif 'wellsfargo' in source and 'favorite' in content:
                print("🎯 WELLS FARGO FAVORITE PROJECT!")
            elif 'astro' in source:
                print("⚠️  Astro website (generic)")
            else:
                print("📄 Other content")
                
            print(f"Content preview: {doc.page_content[:200]}...")
            print("-" * 40)
            
        # Test the full pipeline with GPT
        print(f"\n🤖 GPT RESPONSE:")
        prompt = PromptTemplate(
            template="Use the following context to answer the question. Answer as TC Heiner in first person.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:",
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=retriever_config.get('max_tokens', 150),
                openai_api_key=os.environ['OPENAI_API_KEY']
            ),
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        result = qa_chain.invoke({"query": question})
        print(result["result"])
        
    except Exception as e:
        print(f"Error testing {strategy_name}: {e}")
        import traceback
        traceback.print_exc()

# Test all strategies
strategies = {
    "DEFAULT (Current)": {
        'search_type': 'similarity',
        'k': 5,
        'score_threshold': 0.5,
        'max_tokens': 150
    },
    "MORE CHUNKS": {
        'search_type': 'similarity', 
        'k': 10,
        'score_threshold': 0.4,
        'max_tokens': 200
    },
    "MMR (Diverse)": {
        'search_type': 'mmr',
        'k': 8,
        'fetch_k': 20,
        'lambda_mult': 0.7,
        'max_tokens': 200
    },
    "MMR (More Similar)": {
        'search_type': 'mmr',
        'k': 8,
        'fetch_k': 20,
        'lambda_mult': 0.9,  # More similarity, less diversity
        'max_tokens': 200
    },
    "MORE CHUNKS + LOWER THRESHOLD": {
        'search_type': 'similarity',
        'k': 12,
        'score_threshold': 0.3,  # Much more permissive
        'max_tokens': 250
    }
}

print(f"Testing question: {question}")
print(f"Total vectorstore documents: Loading...")

for strategy_name, config in strategies.items():
    test_strategy(strategy_name, config)

print(f"\n{'='*60}")
print("TESTING COMPLETE!")
print("Look for strategies that surface ManaBurn/Web Crawler content")
print(f"{'='*60}")