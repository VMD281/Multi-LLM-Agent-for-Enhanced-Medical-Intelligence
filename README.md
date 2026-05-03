# Multi-LLM Medical Agent System

## Project Description
TThis project implements a **Multi-LLM Medical Agent System** designed to answer complex medical questions. It achieves this by leveraging a central Large Language Model (LLM) for high-level reasoning and synthesis, integrated with external, specialized data sources: a web search engine and a medical literature database (PubMed). The system demonstrates how an intelligent, LLM-powered agent can orchestrate external tools and synthesize diverse information to provide comprehensive and informed responses to user queries.


## Architecture
The system comprises the following key components:
- **`MedicalAgent`**: The core orchestrator and the primary **LLM-powered agent** of the system. It interacts with the user, delegates information retrieval tasks to specialized services, and critically, uses a powerful LLM to synthesize the retrieved data into a coherent, comprehensive answer.
- **`MCPClient` (Model Context Protocol Client)**: A communication layer responsible for sending structured requests to various services (agents), ensuring a standardized way of exchanging information.
- **`WebSearchMCPService`**: A service that performs web searches (integrated with Brave Search API) to retrieve general medical information.
- **`PubMedMCPService`**: A service that queries the PubMed database (integrated with NCBI E-utilities API) to access authoritative peer-reviewed medical literature.
- **LLM Integration**: The `MedicalAgent` directly utilizes a Generative AI model (Claude) not just for generating text, but for performing complex **reasoning, information extraction, summarization, and synthesis** from the raw data returned by the search services. This central LLM makes the `MedicalAgent` intelligent and forms the "Multi-LLM" aspect of the system.

The system flow is: User Query -> **MedicalAgent (LLM)** -> (WebSearch + PubMed Services as tools) -> Raw Results (displayed to user for transparency) -> **MedicalAgent (LLM for Synthesis)** -> Final Answer to User.

## Setup Instructions

### 1. Clone the Repository / Extract the ZIP File
If you received a ZIP file, extract its contents to your desired project directory.

### 2. Create and Activate a Python Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.
```bash
# Navigate into your project directory
cd your-project-folder-name # e.g., cd multi-llm_agent_system

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows (Command Prompt):
# venv\Scripts\activate.bat
# On Windows (PowerShell):
# venv\Scripts\Activate.ps1