from logger import logger
from fastapi import APIRouter, HTTPException
from chatbot.models import QueryRequest, QueryResponse
from chatbot.services import ask_question

# Create a router
router = APIRouter()

# Chatbot query endpoint
@router.post("/chat", response_model=QueryResponse, tags=["Chatbot"])
async def chat(request: QueryRequest):
    question = request.question
    try:
        answer, sources = ask_question(question)
        return {"answer": answer, "sources": [source.metadata["source"] for source in sources]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
