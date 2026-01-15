# Normal imports - no more lazy loading needed with container images
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from typing import List
import re
from datetime import datetime

from dotenv import load_dotenv
import os
import json

from . import content_ingest

load_dotenv()
openai_key = os.environ.get("OPENAI_API_KEY")

# Retrieval configuration from environment variables
RETRIEVAL_STRATEGY = os.environ.get("RETRIEVAL_STRATEGY", "default")  # default, more_chunks, mmr, custom_scoring
RETRIEVAL_K = int(os.environ.get("RETRIEVAL_K", "5"))  # Number of chunks to retrieve
SCORE_THRESHOLD = float(os.environ.get("SCORE_THRESHOLD", "0.5"))  # Similarity threshold
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "600"))  # GPT response length - increased for fuller responses
LAMBDA_MULT = float(os.environ.get("LAMBDA_MULT", "0.7"))  # MMR balance (0.7=similarity, 0.3=diversity)  
FETCH_K = int(os.environ.get("FETCH_K", "20"))  # MMR candidate pool size

# Custom Scoring configuration
RECENCY_BOOST = float(os.environ.get("RECENCY_BOOST", "0.1"))
IMPRESSIVE_KEYWORDS_BOOST = float(os.environ.get("IMPRESSIVE_KEYWORDS_BOOST", "0.1"))
TECHNICAL_TERMS_BOOST = float(os.environ.get("TECHNICAL_TERMS_BOOST", "0.1"))
PRIDE_TERMS_BOOST = float(os.environ.get("PRIDE_TERMS_BOOST", "0.1"))

# Define the path where the FAISS index will be saved (inside the chatbot directory)
chatbot_dir = os.path.dirname(__file__)
faiss_index_path = os.path.join(chatbot_dir, "faiss_index")
blog_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/content'))

# Load scoring keywords
def load_scoring_keywords():
    """Load keyword lists from JSON file"""
    keywords_file = os.path.join(os.path.dirname(__file__), "../scoring_keywords.json")
    try:
        with open(keywords_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Keywords file not found at {keywords_file}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in keywords file at {keywords_file}")
        return {}

SCORING_KEYWORDS = load_scoring_keywords()

class CustomScoringRetriever(BaseRetriever):
    """Custom retriever that boosts scores for recent/impressive projects using keyword lists"""
    
    def __init__(self, vectorstore: FAISS, k: int = 5, **kwargs):
        super().__init__(**kwargs)
        # Store as private attributes to avoid Pydantic validation
        self._vectorstore = vectorstore
        self._k = k
        self._current_year = datetime.now().year
    
    @property
    def vectorstore(self):
        return self._vectorstore
    
    @property 
    def k(self):
        return self._k
        
    @property
    def current_year(self):
        return self._current_year
    
    def _extract_years_from_content(self, content: str) -> List[int]:
        """Extract years from content (startDate, endDate, etc.)"""
        year_patterns = [
            r'\b(20\d{2})-\d{2}-\d{2}\b',  # YYYY-MM-DD format
            r'\b(20\d{2})\b'               # Standalone years
        ]
        
        years = []
        for pattern in year_patterns:
            matches = re.findall(pattern, content)
            years.extend([int(year) for year in matches])
        
        return list(set(years))
    
    def _calculate_recency_boost(self, years: List[int]) -> float:
        """Calculate boost based on proximity to current year"""
        if not years:
            return 0
            
        most_recent_year = max(years)
        years_ago = self.current_year - most_recent_year
        
        # Scale by RECENCY_BOOST environment variable
        base_boost = RECENCY_BOOST
        if years_ago <= 1:      # Current or last year
            return base_boost * 3.0
        elif years_ago <= 2:    # 2 years ago
            return base_boost * 2.0
        elif years_ago <= 3:    # 3 years ago  
            return base_boost * 1.0
        elif years_ago <= 5:    # 3-5 years ago
            return base_boost * 0.5
        else:                   # Older than 5 years
            return 0
    
    def _calculate_keyword_boost(self, content: str, metadata: dict = None) -> float:
        """Calculate boost based on keyword matches from JSON file and metadata tags"""
        content_lower = content.lower()
        total_boost = 0
        
        # Also check tags from metadata
        searchable_text = content_lower
        if metadata:
            # Add tags to searchable text
            tags = metadata.get('tags', [])
            if isinstance(tags, list):
                searchable_text += " " + " ".join(str(tag).lower() for tag in tags)
            
            # Add other metadata fields that might be relevant
            for field in ['title', 'company', 'description']:
                if field in metadata and metadata[field]:
                    searchable_text += " " + str(metadata[field]).lower()
        
        # Check all keyword categories
        keyword_categories = {
            'pride_terms': PRIDE_TERMS_BOOST,
            'management_skills': IMPRESSIVE_KEYWORDS_BOOST * 1.5,  # Management gets extra boost
            'leadership_keywords': IMPRESSIVE_KEYWORDS_BOOST * 1.5,
            'executive_leadership': IMPRESSIVE_KEYWORDS_BOOST * 2.0,  # Highest boost for executive
            'people_management': IMPRESSIVE_KEYWORDS_BOOST * 1.5,
            'project_program_management': IMPRESSIVE_KEYWORDS_BOOST * 1.2,
            'engineering_management': IMPRESSIVE_KEYWORDS_BOOST * 1.3,
            'founding_engineer': IMPRESSIVE_KEYWORDS_BOOST * 1.4,
            'product_engineer': IMPRESSIVE_KEYWORDS_BOOST * 1.2,
            'director_vp_concerns': IMPRESSIVE_KEYWORDS_BOOST * 2.0,
            'business_impact': TECHNICAL_TERMS_BOOST * 1.3,
            'technical_skills': TECHNICAL_TERMS_BOOST,
            'soft_skills': TECHNICAL_TERMS_BOOST * 0.8
        }
        
        for category, boost_multiplier in keyword_categories.items():
            if category in SCORING_KEYWORDS:
                keywords = SCORING_KEYWORDS[category]
                matches = sum(1 for keyword in keywords if keyword.lower() in searchable_text)
                if matches > 0:
                    # Boost increases with number of matches but with diminishing returns
                    category_boost = boost_multiplier * min(matches * 0.3, 1.0)
                    total_boost += category_boost
        
        return total_boost
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        # Get more candidates than we need
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=15)
        
        # Apply custom scoring boosts
        for doc, score in docs_with_scores:
            content = doc.page_content
            metadata = doc.metadata
            
            # Calculate boosts
            years = self._extract_years_from_content(content)
            recency_boost = self._calculate_recency_boost(years)
            keyword_boost = self._calculate_keyword_boost(content, metadata)
            
            total_boost = recency_boost + keyword_boost
            
            # Store metadata for debugging
            doc.metadata['boosted_score'] = score - total_boost  # Lower is better for FAISS
            doc.metadata['original_score'] = score
            doc.metadata['total_boost'] = total_boost
            doc.metadata['recency_boost'] = recency_boost
            doc.metadata['keyword_boost'] = keyword_boost
            doc.metadata['years_found'] = years
        
        # Sort by boosted score and take top k
        docs_with_scores.sort(key=lambda x: x[0].metadata['boosted_score'])
        return [doc for doc, _ in docs_with_scores[:self.k]]

prompt_template = """
You are TC Heiner, having a natural conversation about your career journey. Your goal is to help people understand your capabilities, growth, and what you bring to technical leadership roles.

COMMUNICATION STYLE:
- Speak conversationally and warmly - like chatting with a recruiter or hiring manager
- Share the reasoning behind your decisions and what you learned
- Explain what problems you were solving and why they mattered
- Show enthusiasm for meaningful work

STRATEGIC POSITIONING (DO THIS):
- Connect patterns across your documented experiences to show career progression
- Highlight how skills from different roles complement each other
- Explain what your career trajectory reveals about your capabilities
- Position yourself for technical leadership conversations
- Draw insights from multiple documented experiences to answer strategic questions
- Example: "My progression from developer to staff engineer to founding engineer shows..."
- Example: "Working with both Python and Java across multiple companies demonstrates..."

STAY GROUNDED IN FACTS (NEVER DO THIS):
- Do NOT invent specific projects, companies, or technologies not in the context
- Do NOT add team sizes, budgets, or metrics not documented
- Do NOT claim expertise in technologies/domains not mentioned in context
- If asked about something not documented: "I haven't written much about that" or "That's not an area I've documented yet"

THE DISTINCTION:
✅ "My experience across Wells Fargo, ManaBurn, and Myndsens shows I adapt well to different company stages"
❌ "I also worked with Kubernetes at Wells Fargo" (if not in context)

ABOUT YOU:
17+ years in software engineering. Progression: developer → staff engineer at Wells Fargo → Founding Engineer at ManaBurn → Cloud Architect at Myndsens. Expertise in Python, Java, AWS, AI/ML, containerization, technical leadership.

When referencing blog posts, include links: [Title](https://tcheiner.com/posts/slug)

Context from your documented work:
{context}

Question: {question}

Response (strategic but accurate):"""
def rebuild_vectorstore():
    """
    Rebuilds the FAISS vectorstore from new/updated documents.
    """
    documents = content_ingest.load_documents_for_embedding()
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    if documents:
        print(f"Embedding {len(documents)} new/updated documents...")
        if not os.path.exists(os.path.join(faiss_index_path, "index.faiss")):
            # Create new FAISS index
            vectorstore = FAISS.from_documents(documents, embeddings)
        else:
            # Load existing index and add new docs
            vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
            vectorstore.add_documents(documents)
        # Save updated index
        vectorstore.save_local(faiss_index_path)
        # Update the last rebuild time
        content_ingest.update_last_rebuild_time()
        return vectorstore
    else:
        print("No new or updated documents to embed.")
        # Load the existing index
        vectorstore = FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)
        return vectorstore

def get_local_vectorstore():
    """
    Loads the local FAISS vectorstore from disk.
    """
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

def get_lambda_vectorstore():
    LAYER_PATH = "/opt/python/faiss_index"  # /opt is where Lambda layers are mounted
    faiss_index_path = LAYER_PATH
    openai_key = os.environ.get("OPENAI_API_KEY")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return FAISS.load_local(faiss_index_path, embeddings, allow_dangerous_deserialization=True)

def get_qa_chain(vectorstore):
    """
    Get QA chain using environment variable configuration
    """
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    # Configure retriever based on environment variables
    if RETRIEVAL_STRATEGY == "more_chunks":
        # Strategy 2: Just get more chunks
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": RETRIEVAL_K,
                "score_threshold": SCORE_THRESHOLD
            }
        )
    elif RETRIEVAL_STRATEGY == "mmr":
        # Strategy 3: MMR for diversity
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": RETRIEVAL_K,
                "fetch_k": FETCH_K,
                "lambda_mult": LAMBDA_MULT
            }
        )
    elif RETRIEVAL_STRATEGY == "custom_scoring":
        # Strategy 4: Custom scoring with keyword boosts
        retriever = CustomScoringRetriever(vectorstore=vectorstore, k=RETRIEVAL_K)
    else:
        # Default similarity search
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": RETRIEVAL_K,
                "score_threshold": SCORE_THRESHOLD
            }
        )
    
    return RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.6,  # Balanced for strategic connections without hallucination
            max_tokens=MAX_TOKENS,
            openai_api_key=openai_key
        ),
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

def query_vectorstore(question):
    """
    Queries the vectorstore with the given question and returns the answer and sources.
    """
    # Check if running in Lambda environment
    if os.path.exists("/opt/python/faiss_index"):
        vectorstore = get_lambda_vectorstore()
    else:
        vectorstore = get_local_vectorstore()
    
    qa_chain = get_qa_chain(vectorstore)
    response = qa_chain.invoke({"query": question})
    answer = response["result"]
    sources = response["source_documents"]
    return answer, sources

def get_mock_response(question: str) -> str:
    """
    Mock response generator for chatbot queries.
    """
    if "hello" in question.lower():
        return "Hi there! How can I help you today?"
    elif "help" in question.lower():
        return "Sure, let me assist you with that."
    else:
        return "Sorry, I'm just a mock bot and don't have a real answer for that."


