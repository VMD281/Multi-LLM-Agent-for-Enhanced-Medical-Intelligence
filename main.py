import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

load_dotenv()

app = FastAPI(
    title="Multi-Agent Medical Intelligence System",
    description="""
    A multi-agent AI system using Claude LLM with RAG to retrieve medical evidence 
    from PubMed and BraveSearch. Orchestrated with LangGraph & MCP for multi-step 
    workflows and context sharing.
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes import router as api_router
app.include_router(api_router, prefix="/api/v1", tags=["Medical Agent"])


@app.get("/")
async def root():
    return {
        "name": "Multi-Agent Medical Intelligence System",
        "version": "1.0.0",
        "description": "Medical Q&A powered by LangChain, LangGraph, and Claude LLM",
        "endpoints": {
            "health": "/api/v1/health",
            "parse_query": "/api/v1/parse",
            "medical_query": "/api/v1/query",
            "synthesize": "/api/v1/synthesize",
            "docs": "/docs"
        }
    }


def check_api_keys():
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("NCBI_API_KEY"):
        missing.append("NCBI_API_KEY")
    if not os.getenv("BRAVE_SEARCH_API_KEY"):
        print("[INFO] BRAVE_SEARCH_API_KEY not set - web search will be limited")
    
    if missing:
        print(f"[WARNING] Missing API keys: {', '.join(missing)}")
        print("The server will start, but queries will fail until keys are set.")
        print("Visit /docs for API documentation.")
    else:
        print("[OK] All required API keys configured")
    
    return True


if __name__ == "__main__":
    check_api_keys()
    print("\nStarting Multi-Agent Medical Intelligence System...")
    print("API Documentation: http://0.0.0.0:5000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
