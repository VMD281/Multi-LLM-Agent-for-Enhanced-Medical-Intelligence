import os
import requests
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.documents import Document

class BraveSearchService:
    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        self.search_url = "https://api.search.brave.com/res/v1/web/search"
        self.max_results = 5

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return [{"error": "BRAVE_SEARCH_API_KEY not configured"}]

        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }
            params = {
                "q": query + " medical health",
                "count": self.max_results
            }

            response = requests.get(self.search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            if "web" in data and "results" in data["web"]:
                for r in data["web"]["results"]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("description", ""),
                        "source": "Web Search"
                    })

            return results

        except requests.RequestException as e:
            return [{"error": f"Brave search failed: {str(e)}"}]

    def to_documents(self, results: List[Dict[str, Any]]) -> List[Document]:
        docs = []
        for r in results:
            if "error" not in r:
                docs.append(Document(
                    page_content=f"Title: {r['title']}\n\nContent: {r['snippet']}",
                    metadata={"source": r["url"]}
                ))
        return docs

@tool
def search_web(query: str) -> str:
    """Search the web for medical information using Brave Search.
    
    Args:
        query: Medical search query
        
    Returns:
        String with formatted search results
    """
    service = BraveSearchService()
    results = service.search(query)
    
    if not results:
        return "No web results found."
    
    if "error" in results[0]:
        return f"Error: {results[0]['error']}"
    
    output = []
    for i, r in enumerate(results, 1):
        output.append(f"{i}. {r['title']}")
        output.append(f"   URL: {r['url']}")
        output.append(f"   Summary: {r['snippet']}")
        output.append("")
    
    return "\n".join(output)
