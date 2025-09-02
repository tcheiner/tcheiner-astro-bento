from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

class AskRequest(BaseModel):
    question: str
    userApiKey: str = None  # Optional user API key

class AskResponse(BaseModel):
    answer: str
    sources: List[str]