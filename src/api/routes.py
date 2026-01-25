import os
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.schemas import QueryRequest, MedicalResponse, SearchResult

router = APIRouter()

orchestrator = None

def check_required_keys():
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("NCBI_API_KEY"):
        missing.append("NCBI_API_KEY")
    return missing

def get_orchestrator():
    global orchestrator
    missing = check_required_keys()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Missing required API keys: {', '.join(missing)}. Please configure them in your environment."
        )
    if orchestrator is None:
        from src.agents.orchestrator import MedicalAgentOrchestrator
        orchestrator = MedicalAgentOrchestrator()
    return orchestrator


class HealthResponse(BaseModel):
    status: str
    version: str
    api_keys_configured: bool
    missing_keys: List[str]


class QueryParseRequest(BaseModel):
    raw_query: str = Field(..., description="Raw user query to parse")


class ParsedQuery(BaseModel):
    original: str
    medical_terms: List[str]
    query_type: str
    refined_query: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    missing = check_required_keys()
    return HealthResponse(
        status="healthy" if not missing else "degraded",
        version="1.0.0",
        api_keys_configured=len(missing) == 0,
        missing_keys=missing
    )


@router.post("/parse", response_model=ParsedQuery)
async def parse_query(request: QueryParseRequest):
    medical_keywords = [
        "symptoms", "treatment", "diagnosis", "medication", "disease",
        "condition", "therapy", "causes", "prevention", "side effects",
        "research", "study", "clinical", "patient", "doctor"
    ]
    
    query_lower = request.raw_query.lower()
    found_terms = [kw for kw in medical_keywords if kw in query_lower]
    
    if any(word in query_lower for word in ["what is", "what are", "define"]):
        query_type = "definition"
    elif any(word in query_lower for word in ["how to", "treatment", "cure"]):
        query_type = "treatment"
    elif any(word in query_lower for word in ["symptoms", "signs"]):
        query_type = "symptoms"
    elif any(word in query_lower for word in ["research", "study", "evidence"]):
        query_type = "research"
    else:
        query_type = "general"
    
    refined = request.raw_query
    if not any(term in query_lower for term in ["medical", "health", "clinical"]):
        refined = f"{request.raw_query} medical health"
    
    return ParsedQuery(
        original=request.raw_query,
        medical_terms=found_terms,
        query_type=query_type,
        refined_query=refined
    )


@router.post("/query", response_model=MedicalResponse)
async def process_medical_query(request: QueryRequest):
    start_time = time.time()
    
    try:
        orch = get_orchestrator()
        result = orch.run(request.query)
        
        processing_time = time.time() - start_time
        
        pubmed_sources = []
        for r in result.get("pubmed_results", []):
            if isinstance(r, dict) and "error" not in r:
                pubmed_sources.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("snippet", "")[:300],
                    source="PubMed",
                    authors=r.get("authors"),
                    publication_year=r.get("publication_year")
                ))
        
        web_sources = []
        for r in result.get("web_results", []):
            if isinstance(r, dict) and "error" not in r:
                web_sources.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("snippet", "")[:300],
                    source="Web"
                ))
        
        return MedicalResponse(
            query=request.query,
            answer=result.get("answer", "Unable to generate answer"),
            pubmed_sources=pubmed_sources,
            web_sources=web_sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_evidence(
    query: str,
    pubmed_summary: str,
    web_summary: str
):
    try:
        orch = get_orchestrator()
        
        answer = orch.synthesis_chain.invoke({
            "query": query,
            "pubmed_summary": pubmed_summary,
            "web_summary": web_summary
        })
        
        return {
            "query": query,
            "synthesized_answer": answer
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
