from fastapi import APIRouter, HTTPException
from .models import QueryRequest, QueryResponse
from .services import query_vectorstore

# Create a router
router = APIRouter()

# Chatbot query endpoint
@router.post("/chat", response_model=QueryResponse, tags=["Chatbot"])
async def chat(request: QueryRequest):
    question = request.question
    try:
        answer, sources = query_vectorstore(question)
        return {"answer": answer, "sources": [source.metadata["source"] for source in sources]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
