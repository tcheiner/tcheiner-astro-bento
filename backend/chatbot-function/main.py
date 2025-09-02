import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes import router
from services import query_vectorstore
from pydantic import BaseModel
from typing import List
from mangum import Mangum
from models import AskRequest, AskResponse

# LangChain and OpenAI imports - REMOVED to prevent import timing issues
# These will be imported lazily inside functions when layers are fully loaded

# Global variables for caching
_vectorstore = None
_qa_chain = None

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

def get_vectorstore():
    """Lazy load and cache the FAISS vectorstore from appropriate location."""
    global _vectorstore
    if _vectorstore is None:
        # Lazy import to avoid layer loading issues
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Determine the correct path based on environment
        if os.path.exists("/opt/python/faiss_index"):
            # Lambda environment - layer path
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

def get_qa_chain():
    """Lazy load and cache the RetrievalQA chain."""
    global _qa_chain
    if _qa_chain is None:
        # Lazy import to avoid layer loading issues
        from langchain_openai import ChatOpenAI
        from langchain.prompts import PromptTemplate
        from langchain.chains import RetrievalQA
        
        # Prompt template
        prompt_template = """
            You are TC Heiner. Use the following context to answer the user's question.
            If you don't know the answer, say you have that data. Do NOT make anything up.

            Context:
            {context}

            Question:
            {question}

            Answer:
            """
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        
        # Create the RetrievalQA chain
        _qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY),
            retriever=get_vectorstore().as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
    return _qa_chain

# Create FastAPI app
app = FastAPI(title="Chatbot Backend", version="1.0.0")

# Mangum handler for AWS Lambda
handler = Mangum(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Allow all origins (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router)

# Log a message when the app starts
@app.on_event("startup")
async def startup_event():
    print("TC Heiner Chatbot is starting up...")

# Log a message when the app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    print("TC Heiner Chatbot is shutting down...")


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest):
    # Use the lazy-loaded QA chain
    qa_chain = get_qa_chain()
    result = qa_chain({"query": request.question})
    answer = result["result"]
    sources = result["source_documents"]
    return AskResponse(answer=answer, sources=[doc.metadata.get("source", "") for doc in sources])
