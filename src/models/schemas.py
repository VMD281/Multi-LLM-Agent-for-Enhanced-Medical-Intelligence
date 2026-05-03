from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class AgentType(str, Enum):
    PUBMED = "pubmed"
    WEB_SEARCH = "web_search"
    SYNTHESIZER = "synthesizer"

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    authors: Optional[str] = None
    publication_year: Optional[str] = None

class QueryRequest(BaseModel):
    query: str = Field(..., description="Medical question to answer")
    include_pubmed: bool = Field(default=True, description="Search PubMed")
    include_web: bool = Field(default=True, description="Search web")

class AgentState(BaseModel):
    query: str
    pubmed_results: List[SearchResult] = []
    web_results: List[SearchResult] = []
    synthesized_answer: str = ""
    current_agent: AgentType = AgentType.PUBMED
    error: Optional[str] = None
    completed: bool = False

class MedicalResponse(BaseModel):
    query: str
    answer: str
    pubmed_sources: List[SearchResult]
    web_sources: List[SearchResult]
    processing_time: float
