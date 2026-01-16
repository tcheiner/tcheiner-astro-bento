from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

class AskRequest(BaseModel):
    question: str
    userApiKey: Optional[str] = None  # Optional user API key for paid tier

class AskResponse(BaseModel):
    answer: str
    sources: List[str]