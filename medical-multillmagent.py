import os
from dotenv import load_dotenv
import json
import time
from abc import ABC, abstractmethod
import requests
from anthropic import Anthropic
import xml.etree.ElementTree as ET
import re
import traceback

load_dotenv()

# --- Model Context Protocol (MCP) ---
class MCPService(ABC):
    """
    Abstract base class for all Model Context Protocol services.
    Defines the contract for services.
    """
    def __init__(self, service_name: str):
        self.service_name = service_name

    @abstractmethod
    def process_request(self, request: dict) -> dict:
        """
        Processes an incoming request according to the MCP.
        """
        pass

class MCPClient:
    """
    Client responsible for sending requests to MCP services.
    """
    def __init__(self, services: dict[str, MCPService]):
        """
        Initializes the client with a dictionary of available services.
        Key: service_name, Value: MCPService instance.
        """
        self.services = services

    def send_request(self, service_name: str, query: str, context: dict = None) -> dict:
        
        if service_name not in self.services:
            return {
                "status": "failure",
                "message": f"Service '{service_name}' not found.",
                "error": "Service not available"
            }

        request_payload = {
            "service_name": service_name,
            "query": query,
            "context": context if context is not None else {}
        }
        print(f"[MCPClient] Sending request to {service_name}: {json.dumps(request_payload)}")
        response = self.services[service_name].process_request(request_payload)
        print(f"[MCPClient] Received response from {service_name}: {json.dumps(response)}")
        return response

# --- MCP Service Implementations ---

class WebSearchMCPService(MCPService):
    def __init__(self):
        super().__init__("web_search")
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            print("[WebSearchMCPService] WARNING: BRAVE_SEARCH_API_KEY not set. Using simulated web search results.")
        else:
            self.search_url = "https://api.search.brave.com/res/v1/web/search"
            
    def process_request(self, request: dict) -> dict:
        query = request.get("query")
        if not query:
            return {
                "status": "failure",
                "message": "Missing 'query' in request.",
                "error": "Invalid request"
            }

        
        
        print(f"[WebSearchMCPService] Performing REAL Brave Search for: '{query}'")
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": query,
            "count": 5 # Number of results to fetch
        }

        results_list = []
        try:
            response = requests.get(self.search_url, headers=headers, params=params, timeout=10) 
            response.raise_for_status()
            data = response.json()

            if data and 'web' in data and 'results' in data['web']:
                for r in data['web']['results']:
                    results_list.append({
                        "title": r.get('title'),
                        "url": r.get('url'),
                        "snippet": r.get('description')
                    })
            return {
                "status": "success",
                "message": "Real Brave search completed successfully.",
                "results": results_list
            }
        except requests.exceptions.Timeout:
            return {
                "status": "failure",
                "message": "Web search request timed out.",
                "error": "Timeout"
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "failure",
                "message": f"Brave Search API call failed: {e}",
                "error": "API error"
            }

class PubMedMCPService(MCPService):
    """
    Integrates with the real NCBI E-utilities API for PubMed searches.
    Uses esearch.fcgi to get IDs and efetch.fcgi to fetch abstracts.
    Requires an NCBI_API_KEY to be set in the .env file.
    """
    def __init__(self):
        super().__init__("pubmed_search")
        self.esearch_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.efetch_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.api_key = os.getenv("NCBI_API_KEY")
        self.max_results = 5 # Number of articles to retrieve

        if not self.api_key:
            raise ValueError(
                "NCBI_API_KEY environment variable not set. "
                "PubMedMCPService requires an NCBI API key for operation. "
                "Please add NCBI_API_KEY='your_key_here' to your .env file."
            )
        print("[PubMedMCPService] NCBI_API_KEY successfully loaded and will be used for all PubMed requests.")

    def process_request(self, request: dict) -> dict:
        print("[PubMedMCPService] Entering process_request method.") # Debug print

        query = request.get("query")
        if query is None:
            print("[PubMedMCPService] ERROR: 'query' key is missing from the request dictionary.")
            return {
                "status": "failure",
                "message": "Missing 'query' in request.",
                "error": "Invalid request"
            }
        if not isinstance(query, str):
            print(f"[PubMedMCPService] ERROR: 'query' value is not a string. Type: {type(query)}")
            return {
                "status": "failure",
                "message": "Invalid 'query' type in request. Expected string.",
                "error": "Invalid request type"
            }
        if not query.strip():
            print("[PubMedMCPService] WARNING: 'query' is an empty or whitespace-only string.")
            return {
                "status": "failure",
                "message": "Empty query received.",
                "error": "Invalid request content"
            }

        pmids = []
        try:
            # --- Step 1: Search for PMIDs using esearch ---
            esearch_params = {
                "db": "pubmed",
                "term": query,
                "retmax": self.max_results,
                "retmode": "json",
                "api_key": self.api_key
            }

            print(f"[PubMedMCPService] Searching PubMed for IDs with query: '{query}'")
            print(f"[PubMedMCPService] ESearch Request URL: {self.esearch_base_url}?{requests.compat.urlencode(esearch_params)}")

            esearch_response = requests.get(self.esearch_base_url, params=esearch_params, timeout=15)
            esearch_response.raise_for_status()
            esearch_data = esearch_response.json()

            print(f"[PubMedMCPService] Raw ESearch JSON Response: {json.dumps(esearch_data, indent=2)}")

            pmids = esearch_data.get("esearchresult", {}).get("idlist", [])

            print(f"[PubMedMCPService] Extracted PMIDs: {pmids}")

            if not pmids:
                print(f"[PubMedMCPService] No PMIDs found for query: '{query}' (idlist was empty after parsing)")
                return {
                    "status": "success",
                    "message": "No relevant PubMed articles found.",
                    "results": []
                }

        except requests.exceptions.Timeout:
            print(f"[PubMedMCPService] ESearch request timed out for query: '{query}'")
            return { "status": "failure", "message": "PubMed esearch request timed out.", "error": "Timeout" }
        except requests.exceptions.RequestException as e:
            print(f"[PubMedMCPService] ESearch API call failed for query: '{query}': {e}")
            return { "status": "failure", "message": f"PubMed esearch API call failed: {e}", "error": "API error" }
        except json.JSONDecodeError as e:
            print(f"[PubMedMCPService] Error decoding JSON from ESearch response for query: '{query}': {e}. Response text: {esearch_response.text[:200]}...")
            return { "status": "failure", "message": f"Error decoding JSON from esearch response: {e}", "error": "JSON parse error" }
        except Exception as e:
            print(f"[PubMedMCPService] An unexpected error occurred during ESearch processing for query '{query}': {e}")
            traceback.print_exc()
            return { "status": "failure", "message": f"An unexpected error occurred during ESearch: {e}", "error": "Unexpected error" }


        # --- Step 2: Fetch abstracts for retrieved PMIDs using efetch ---
        articles_data = [] 
        if pmids:
            try:
                efetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "xml",
                    "api_key": self.api_key
                }

                print(f"[PubMedMCPService] EFetch Request URL: {self.efetch_base_url}?{requests.compat.urlencode(efetch_params)}")
                print(f"[PubMedMCPService] Fetching abstracts for PMIDs: {', '.join(pmids)}")

                efetch_response = requests.get(self.efetch_base_url, params=efetch_params, timeout=30)
                efetch_response.raise_for_status()
                efetch_xml_data = efetch_response.text

                
                print(f"[PubMedMCPService] Raw EFetch XML Response (first 500 chars): {efetch_xml_data[:500]}...")


                # --- XML parsing ---
                root = ET.fromstring(efetch_xml_data)
                pubmed_articles = root.findall(".//PubmedArticle")

                for article_elem in pubmed_articles:
                    pmid = article_elem.findtext(".//PMID", default="N/A")

                    # Extract Article Title
                    title_elem = article_elem.find(".//ArticleTitle")
                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else "N/A"
                    if title == "N/A" and title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()


                    # Extract Abstract
                    abstract_texts = article_elem.findall(".//Abstract/AbstractText")
                    abstract_parts = []
                    for abs_text_elem in abstract_texts:
                        if abs_text_elem is not None and abs_text_elem.text:
                            label = abs_text_elem.get("Label")
                            if label:
                                abstract_parts.append(f"**{label.strip()}:** {abs_text_elem.text.strip()}")
                            else:
                                abstract_parts.append(abs_text_elem.text.strip())

                    abstract_snippet = "\n\n".join(abstract_parts) if abstract_parts else "No abstract available."

                    # Extract Authors
                    authors = []
                    author_list_elem = article_elem.find(".//AuthorList")
                    if author_list_elem is not None:
                        for author_elem in author_list_elem.findall(".//Author"):
                            last_name = author_elem.findtext("LastName", default="")
                            fore_name = author_elem.findtext("ForeName", default="")
                            initials = author_elem.findtext("Initials", default="")
                            
                            full_name_parts = []
                            if fore_name:
                                full_name_parts.append(fore_name.strip())
                            if initials and not fore_name: 
                                full_name_parts.append(initials.strip())
                            if last_name:
                                full_name_parts.append(last_name.strip())
                            
                            author_name = " ".join(full_name_parts).strip()
                            if author_name:
                                authors.append(author_name)
                    
                    authors_str = ", ".join(authors) if authors else "N/A"

                    # Extract Journal and Year
                    journal_title = article_elem.findtext(".//Journal/Title", default="N/A")
                    pub_year = article_elem.findtext(".//Journal/JournalIssue/PubDate/Year", default="N/A")
                    if pub_year == "N/A": 
                        pub_year = article_elem.findtext(".//ArticleDate/Year", default="N/A")

                    # Construct URL if PMID is available
                    article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "N/A" else "N/A"

                   
                    if title != "N/A" or abstract_snippet != "No abstract available.":
                        articles_data.append({
                            "title": title,
                            "url": article_url,
                            "snippet": abstract_snippet, 
                            "source_title": journal_title,
                            "publication_time": pub_year, 
                            "authors": authors_str
                        })
                    else:
                        print(f"[PubMedMCPService] Skipping PMID {pmid} due to missing title and abstract (likely a very recent 'Publisher' entry or incomplete data).")

                print(f"[PubMedMCPService] Successfully parsed {len(articles_data)} articles from EFetch.")

            except requests.exceptions.Timeout:
                print(f"[PubMedMCPService] EFetch request timed out for PMIDs: {', '.join(pmids)}")
                return { "status": "failure", "message": "PubMed efetch request timed out.", "error": "Timeout" }
            except requests.exceptions.RequestException as e:
                print(f"[PubMedMCPService] EFetch API call failed for PMIDs: {', '.join(pmids)}: {e}")
                return { "status": "failure", "message": f"PubMed efetch API call failed: {e}", "error": "API error" }
            except ET.ParseError as e:
                print(f"[PubMedMCPService] Error parsing XML from EFetch response: {e}. Response start: {efetch_xml_data[:500]}...")
                return { "status": "failure", "message": f"Error parsing XML from efetch response: {e}", "error": "XML parse error" }
            except Exception as e:
                print(f"[PubMedMCPService] An unexpected error occurred during PubMed EFetch XML processing for PMIDs {', '.join(pmids)}: {e}")
                traceback.print_exc()
                return { "status": "failure", "message": f"An unexpected error occurred during PubMed EFetch processing: {e}", "error": "Unexpected error" }
            
        
        return {
            "status": "success",
            "message": "PubMed search and fetch completed successfully.",
            "results": articles_data
        }


# --- Medical Agent  ---

class MedicalAgent:
    """
    The main agent that interacts with the user and orchestrates calls
    to various MCP services.
    """
    def __init__(self, mcp_client: MCPClient, claude_api_key: str, llm_model: str = "claude-3-haiku-20240307"):
        self.mcp_client = mcp_client
        self.llm_model = llm_model
        self.client = Anthropic(api_key=claude_api_key) # Initializes Anthropic client

    def _call_llm(self, prompt: str) -> str:
        """
        Calls the Claude LLM with the given prompt.
        """
        print(f"[MedicalAgent] Sending compiled information to Claude LLM for synthesis (using model: {self.llm_model})...")
        try:
            response = self.client.messages.create(
                model=self.llm_model,
                max_tokens=1000, # Max tokens for Claude response 
                temperature=0.7, 
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip() # Claude's response 
        except Exception as e:
            print(f"[MedicalAgent] Error calling Claude LLM: {e}")
            return "An error occurred while generating the LLM response from Claude."


    def answer_medical_question(self, user_query: str) -> str:
        """
        Takes a user's medical question, queries relevant MCP services,
        and synthesizes the answer using an LLM.
        """
        print(f"\n[MedicalAgent] Received user query: '{user_query}'")

        web_results = self.mcp_client.send_request("web_search", user_query)
        pubmed_results = self.mcp_client.send_request("pubmed_search", user_query)
        # --- Displaying Raw Web Search Results ---
        print("\n--- Raw Web Search Results Retrieved ---")
        if web_results["status"] == "success" and web_results["results"]:
            for i, res in enumerate(web_results["results"][:3]): # Limit to top 3 for display
                print(f"  {i+1}. Title: {res.get('title', 'N/A')}")
                print(f"     URL: {res.get('url', 'N/A')}")
                print(f"     Snippet: {res.get('snippet', 'N/A')}")
            if len(web_results["results"]) > 3:
                print(f"  ...and {len(web_results['results']) - 3} more results.")
        else:
            print("  No relevant web results found or an error occurred.")
            if web_results["status"] == "failure":
                print(f"  Error: {web_results['error']}")
        print("-" * 40)

        # --- Displaying Raw PubMed Search Results ---
        print("\n--- Raw PubMed Search Results Retrieved ---")
        if pubmed_results["status"] == "success" and pubmed_results["results"]:
            for i, res in enumerate(pubmed_results["results"][:3]): # Limit to top 3 for display
                print(f"  {i+1}. Title: {res.get('title', 'N/A')}")
                print(f"     Authors: {res.get('authors', 'N/A')}")
                print(f"     Journal: {res.get('journal', 'N/A')}, Year: {res.get('year', 'N/A')}")
                print(f"     PMID: {res.get('pmid', 'N/A')}")
                print(f"     Abstract Snippet: {res.get('abstract_snippet', 'N/A')[:150]}...\n") 
                print(f"  ...and {len(pubmed_results['results']) - 3} more results.")
        else:
            print("  No relevant PubMed results found or an error occurred.")
            if pubmed_results["status"] == "failure":
                print(f"  Error: {pubmed_results['error']}")
        print("-" * 40)

        # Compiling the information for the LLM
        llm_input_parts = [
            f"You are a highly knowledgeable medical assistant. Based on the following information from web search and PubMed, provide a concise and helpful answer to the user's medical question. Focus on synthesizing the key details and directly answering the question.",
            f"\nUser's original question: {user_query}\n\n",
            "--- Web Search Results ---\n"
        ]

        if web_results["status"] == "success" and web_results["results"]:
            for i, res in enumerate(web_results["results"][:3]): # Limit to top 3
                llm_input_parts.append(f"  {i+1}. Title: {res.get('title', 'N/A')}")
                llm_input_parts.append(f"     URL: {res.get('url', 'N/A')}")
                llm_input_parts.append(f"     Snippet: {res.get('snippet', 'N/A')}\n")
        else:
            llm_input_parts.append("  No relevant web results found or an error occurred.\n")

        llm_input_parts.append("\n--- PubMed Search Results ---\n")
        if pubmed_results["status"] == "success" and pubmed_results["results"]:
            for i, res in enumerate(pubmed_results["results"][:3]): # Limit to top 3
                llm_input_parts.append(f"  {i+1}. Title: {res.get('title', 'N/A')}")
                llm_input_parts.append(f"     Authors: {res.get('authors', 'N/A')}")
                llm_input_parts.append(f"     Journal: {res.get('journal', 'N/A')}, Year: {res.get('year', 'N/A')}")
                llm_input_parts.append(f"     PMID: {res.get('pmid', 'N/A')}")
                llm_input_parts.append(f"     Abstract Snippet: {res.get('abstract_snippet', 'N/A')}\n")
        else:
            llm_input_parts.append("  No relevant PubMed results found or an error occurred.\n")

        compiled_prompt = "".join(llm_input_parts)

        # compiled prompt will go to the LLM for synthesis
        final_answer = self._call_llm(compiled_prompt)

        return f"\n--- Final Answer from Medical Agent (Synthesized by Claude LLM) ---\n{final_answer}"

# --- Main Execution ---

if __name__ == "__main__":
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if not claude_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set. Please set it in a .env file or directly.")
        exit()
    # Initialized MCP Services
    web_search_service = WebSearchMCPService()
    pubmed_service = None # Initialize to None
    try:
        pubmed_service = PubMedMCPService()
    except ValueError as e:
        print(f"\n[CRITICAL ERROR] Failed to initialize PubMedMCPService: {e}")
        print("Please ensure your .env file has NCBI_API_KEY='YOUR_KEY' set correctly.")
        print("Exiting application as PubMed search functionality cannot be used.")
        exit()

    # Dictionary of all available services
    all_services = {
        web_search_service.service_name: web_search_service,
    }
    if pubmed_service:
        all_services[pubmed_service.service_name] = pubmed_service


    # Initialized the MCP Client with the available services
    mcp_client = MCPClient(all_services)

    # Initialized the Medical Agent with the MCP Client and Claude API key
    medical_agent = MedicalAgent(mcp_client, claude_api_key=claude_key, llm_model="claude-3-haiku-20240307")

    print("--- Starting Medical Agent System (Type 'quit' or 'exit' to end) ---")

    while True:
        user_input = input("\n[You] Ask a medical question (e.g., 'What are symptoms of flu?', 'Latest research on diabetes'): ")

        if user_input.lower() in ['quit', 'exit']:
            print("--- Exiting Medical Agent System. Goodbye! ---")
            break

        try:
            response = medical_agent.answer_medical_question(user_input)
            print(response)
        except Exception as e:
            print(f"\n[Agent Error] An unexpected error occurred: {e}")
            print("Please try your question again.")

    print("\n--- Medical Agent System Finished ---")
