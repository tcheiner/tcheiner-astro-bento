from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: List[str]