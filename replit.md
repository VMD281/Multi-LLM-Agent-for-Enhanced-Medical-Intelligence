# Multi-LLM Medical Agent System

## Overview
A Python console application that answers medical questions by leveraging Claude LLM for synthesis, integrated with Brave Search and PubMed for information retrieval.

## Architecture
- **MedicalAgent**: Core orchestrator that uses Claude to synthesize answers
- **WebSearchMCPService**: Brave Search API integration for web search
- **PubMedMCPService**: NCBI E-utilities API for PubMed literature search
- **MCPClient**: Communication layer for structured requests to services

## Required Secrets
- `ANTHROPIC_API_KEY` - Claude API key for LLM synthesis (required)
- `NCBI_API_KEY` - NCBI API key for PubMed access (required)
- `BRAVE_SEARCH_API_KEY` - Brave Search API key (optional, but needed for web search)

## Running the Application
- This is a console/terminal application
- Run: `python medical-multillmagent.py`
- The application provides an interactive prompt for medical questions

## Project Structure
```
.
├── medical-multillmagent.py   # Main application
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
└── replit.md                  # Replit-specific notes
```

## Dependencies
- anthropic - Claude API client
- python-dotenv - Environment variable loading
- requests - HTTP requests for APIs
- pydantic - Data validation
