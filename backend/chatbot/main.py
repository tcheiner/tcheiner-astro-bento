"""
FastAPI Main Application - Multi-Agent Chatbot with Legacy Fallback

ARCHITECTURE:
    Two systems coexist with feature flag toggle:
    1. NEW: Multi-agent orchestrator (tag + FAISS + behavioral analysis)
    2. LEGACY: Single QA chain (backward compatibility)

FEATURE FLAG:
    USE_MULTI_AGENT environment variable (default: true)
    - true: Routes through multi-agent orchestrator
    - false: Uses legacy QA chain
    - On error: Automatic fallback to legacy system

DEPLOYMENT:
    - Local: uvicorn chatbot.main:app --reload
    - Lambda: Mangum handler wraps FastAPI app
    - Container: All dependencies bundled in Docker image
"""

import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
# This must happen before any code that reads environment variables
load_dotenv()

# ============================================
# SHARED DEPENDENCIES (both systems use these)
# ============================================
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import RetrievalQA
from pydantic import BaseModel
from typing import List
from mangum import Mangum
from .models import AskRequest, AskResponse
from .sources import format_sources_as_links  # Used by both systems

# ============================================
# LEGACY SYSTEM IMPORTS (backward compatibility)
# ============================================
from .routes import router
from .services import query_vectorstore
from .filters import is_question_about_tc  # Replaced by filter_classifier_agent
from .confidence import calculate_confidence_score  # Not used in multi-agent
from .summarization import summarize_response  # Not used in multi-agent

# ============================================
# CACHING & CONFIGURATION
# ============================================
# Global variables for caching
_vectorstore = None  # Shared by both systems
_qa_chain = None  # Legacy system only
_orchestrator = None  # Multi-agent system only

# Feature flag for multi-agent system
USE_MULTI_AGENT = os.getenv("USE_MULTI_AGENT", "true").lower() == "true"

# Configuration
def get_openai_api_key():
    """Get OpenAI API key from environment or AWS SSM Parameter Store."""
    # Try environment variable first (for local development)
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    # Fallback to AWS SSM Parameter Store
    try:
        import boto3
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name='/myapp/OPENAI_API_KEY',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except ImportError:
        print("boto3 not available - install with 'pip install boto3' to use AWS SSM")
        raise ValueError("OPENAI_API_KEY not found in environment and boto3 not installed for SSM access")
    except Exception as e:
        print(f"Failed to retrieve API key from SSM: {e}")
        raise ValueError("OPENAI_API_KEY not found in environment or SSM Parameter Store")

OPENAI_API_KEY = get_openai_api_key()
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

def get_vectorstore():
    """Get the FAISS vectorstore from appropriate location."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Determine the correct path based on environment
        if os.path.exists("/opt/python/faiss_index"):
            # Lambda environment - layer path (fallback)
            faiss_path = "/opt/python/faiss_index"
        elif os.path.exists("./chatbot/faiss_index"):
            # Local development from backend directory
            faiss_path = "./chatbot/faiss_index"
        elif os.path.exists("./faiss_index"):
            # Running from within chatbot directory
            faiss_path = "./faiss_index"
        else:
            raise FileNotFoundError("FAISS index not found in any expected location")
            
        _vectorstore = FAISS.load_local(
            faiss_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    return _vectorstore

def get_qa_chain(api_key=None):
    """Get the RetrievalQA chain with specified API key."""
    # Use provided API key or default
    openai_key = api_key or OPENAI_API_KEY
    
    # Always create new chain if using user API key to avoid caching issues
    if api_key:
        return _create_qa_chain(openai_key)
    
    # Cache only the default chain
    global _qa_chain
    if _qa_chain is None:
        _qa_chain = _create_qa_chain(openai_key)
    return _qa_chain


def _create_qa_chain(openai_key):
    """Create a new QA chain with the specified OpenAI API key."""
    # Import prompt template from services to ensure consistency
    from .services import prompt_template

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Create the RetrievalQA chain
    return RetrievalQA.from_chain_type(
        llm=ChatOpenAI(
            model="gpt-4o-mini",  # Use GPT-4o-mini for better quality and cost efficiency
            temperature=0.6,  # Balanced for strategic connections without hallucination
            max_tokens=600,   # Increase to 600 tokens for fuller, more complete responses
            openai_api_key=openai_key
        ),
        retriever=get_vectorstore().as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,           # Increase to 5 for more context
                "score_threshold": 0.5  # Lower threshold to include more relevant docs
            }
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )


def get_orchestrator():
    """Get the multi-agent orchestrator (cached)."""
    global _orchestrator
    if _orchestrator is None:
        try:
            from chatbot.orchestrator import MultiAgentOrchestrator
            _orchestrator = MultiAgentOrchestrator()
            print("Multi-agent orchestrator initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize multi-agent orchestrator: {e}")
            return None
    return _orchestrator

# Create FastAPI app
app = FastAPI(title="Chatbot Backend", version="1.0.0")

# Mangum handler for AWS Lambda
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
        "https://localhost:4321",
        "https://tcheiner.com",
        "https://www.tcheiner.com",
        "https://tcheiner.netlify.app",  # Netlify default subdomain
        "https://*.netlify.app",  # Netlify deploy previews
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Root endpoint for health checks
@app.get("/")
async def root():
    return {"status": "TC Heiner Chatbot API", "version": "1.0.0"}

# Log a message when the app starts
@app.on_event("startup")
async def startup_event():
    print("TC Heiner Chatbot is starting up...")

# Log a message when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    print("TC Heiner Chatbot is shutting down...")


@app.options("/ask")
def ask_options():
    from fastapi import Response
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
        }
    )

@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: AskRequest):
    """
    Main chatbot endpoint - routes to multi-agent system or legacy QA chain
    """

    # Feature flag: Use multi-agent system or legacy approach
    if USE_MULTI_AGENT:
        orchestrator = get_orchestrator()
        if orchestrator:
            try:
                # Use new multi-agent orchestrator
                result = await orchestrator.process_question(request.question)

                # Add model note
                model_note = ""
                if request.userApiKey:
                    model_note = "\n\n*Response generated using your API key with multi-agent system*"
                else:
                    model_note = "\n\n*Free response powered by multi-agent AI system*"

                full_answer = result['answer'] + model_note

                response = AskResponse(
                    answer=full_answer,
                    sources=result['sources']
                )

                # Add CORS headers for browser requests
                from fastapi import Response
                return Response(
                    content=response.model_dump_json(),
                    media_type="application/json",
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
                    }
                )

            except Exception as e:
                print(f"Multi-agent system error: {e}")
                # Fall through to legacy system
                pass

    # Legacy system (fallback or if multi-agent disabled)
    # Content filtering - ensure questions are about TC Heiner
    if not is_question_about_tc(request.question):
        response = AskResponse(
            answer="I can only answer questions about TC Heiner's experience, skills, projects, and professional background. Please ask something related to his work or career.",
            sources=[]
        )
        from fastapi import Response
        return Response(
            content=response.model_dump_json(),
            media_type="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
            }
        )

    try:
        # Use the QA chain with appropriate API key
        qa_chain = get_qa_chain(request.userApiKey)
        result = qa_chain.invoke({"query": request.question})
        raw_answer = result["result"]
        sources = result["source_documents"]

        # Only summarize if response is longer than ~150 tokens (roughly 600 characters)
        api_key = request.userApiKey or OPENAI_API_KEY
        if len(raw_answer) > 600:  # Approximate 150 tokens
            summarized_answer = summarize_response(raw_answer, api_key)
        else:
            summarized_answer = raw_answer

        # Format clickable source links
        source_links = format_sources_as_links(sources)

        # Add model note only (remove confidence explanation)
        model_note = ""
        if request.userApiKey:
            model_note = "\n\n*Response generated using your API key with GPT-4o-mini*"
        else:
            model_note = "\n\n*Free response powered by GPT-4o-mini*"

        # Combine all parts (no confidence note)
        full_answer = summarized_answer + source_links + model_note

        response = AskResponse(
            answer=full_answer,
            sources=[doc.metadata.get("source", "") for doc in sources]
        )

    except Exception as e:
        # Handle API key errors gracefully
        error_msg = str(e)
        if "api" in error_msg.lower() and "key" in error_msg.lower():
            response = AskResponse(
                answer="There seems to be an issue with the API key provided. Please check that it's a valid OpenAI API key and try again.",
                sources=[]
            )
        else:
            response = AskResponse(
                answer=f"I encountered an error processing your question: {error_msg}",
                sources=[]
            )

    # Add CORS headers for browser requests
    from fastapi import Response
    return Response(
        content=response.model_dump_json(),
        media_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
        }
    )
