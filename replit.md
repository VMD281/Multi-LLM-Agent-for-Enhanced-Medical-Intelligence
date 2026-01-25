# Multi-Agent Medical Intelligence System

## Overview
A multi-agent AI system using Claude LLM with RAG to retrieve medical evidence from PubMed and BraveSearch. Orchestrated with LangGraph & MCP for multi-step workflows and context sharing. Built with FastAPI microservices for real-time parsing of user queries and synthesis of retrieved evidence.

## Architecture

### Multi-Agent System
- **PubMedRetrievalAgent**: LangChain agent for searching PubMed medical literature
- **WebSearchRetrievalAgent**: LangChain agent for Brave Search web queries
- **MedicalAgentOrchestrator**: LangGraph-based orchestrator managing multi-step workflows
- **SynthesizerAgent**: Claude LLM agent for evidence synthesis

### Technologies
- **LangChain**: Agent framework for retrieval and tool usage
- **LangGraph**: Multi-agent orchestration with state management
- **FastAPI**: RESTful microservices
- **Claude LLM**: Language model for reasoning and synthesis
- **RAG**: Retrieval-Augmented Generation for evidence-based answers

## Required Secrets
- `ANTHROPIC_API_KEY` - Claude API key for LLM (required)
- `NCBI_API_KEY` - NCBI API key for PubMed access (required)
- `BRAVE_SEARCH_API_KEY` - Brave Search API key (optional)

## Project Structure
```
.
├── main.py                     # FastAPI application entry point
├── cli.py                      # Command-line interface
├── medical-multillmagent.py    # Original implementation (preserved)
├── src/
│   ├── agents/
│   │   ├── retrieval_agents.py # LangChain retrieval agents
│   │   └── orchestrator.py     # LangGraph workflow orchestrator
│   ├── services/
│   │   ├── pubmed_service.py   # PubMed API integration
│   │   └── brave_search_service.py # Brave Search integration
│   ├── api/
│   │   └── routes.py           # FastAPI endpoints
│   └── models/
│       └── schemas.py          # Pydantic models
└── requirements.txt
```

## API Endpoints
- `GET /` - System info and endpoints
- `GET /api/v1/health` - Health check
- `POST /api/v1/parse` - Parse user query
- `POST /api/v1/query` - Process medical question
- `POST /api/v1/synthesize` - Synthesize evidence
- `GET /docs` - Swagger documentation

## Running the Application

### FastAPI Server (Web API)
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 5000
```

### CLI Mode
```bash
python cli.py
```

## Workflow
1. User submits medical query
2. Query parsed and refined
3. PubMed agent retrieves research articles
4. Web search agent retrieves web content
5. LangGraph orchestrates agent execution
6. Synthesizer combines evidence into comprehensive answer
7. Response returned with sources and citations

## Recent Changes
- Integrated LangChain for agent-based retrieval
- Added LangGraph for multi-agent orchestration
- Built FastAPI microservices
- Implemented RAG pattern with FAISS
- Added query parsing endpoint
- Created CLI and API interfaces
