import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.documents import Document

class PubMedService:
    def __init__(self):
        self.esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.api_key = os.getenv("NCBI_API_KEY")
        self.max_results = 5

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return [{"error": "NCBI_API_KEY not configured"}]

        try:
            esearch_params = {
                "db": "pubmed",
                "term": query,
                "retmax": self.max_results,
                "retmode": "json",
                "api_key": self.api_key
            }

            response = requests.get(self.esearch_url, params=esearch_params, timeout=15)
            response.raise_for_status()
            data = response.json()

            pmids = data.get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            return self._fetch_abstracts(pmids)

        except requests.RequestException as e:
            return [{"error": f"PubMed search failed: {str(e)}"}]

    def _fetch_abstracts(self, pmids: List[str]) -> List[Dict[str, Any]]:
        try:
            efetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "api_key": self.api_key
            }

            response = requests.get(self.efetch_url, params=efetch_params, timeout=30)
            response.raise_for_status()

            return self._parse_xml(response.text)

        except (requests.RequestException, ET.ParseError) as e:
            return [{"error": f"Failed to fetch abstracts: {str(e)}"}]

    def _parse_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        articles = []
        root = ET.fromstring(xml_data)

        for article_elem in root.findall(".//PubmedArticle"):
            pmid = article_elem.findtext(".//PMID", default="N/A")
            title = article_elem.findtext(".//ArticleTitle", default="N/A")

            abstract_parts = []
            for abs_elem in article_elem.findall(".//Abstract/AbstractText"):
                if abs_elem.text:
                    label = abs_elem.get("Label", "")
                    text = abs_elem.text.strip()
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)

            abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available"

            authors = []
            for author in article_elem.findall(".//Author"):
                fore = author.findtext("ForeName", "")
                last = author.findtext("LastName", "")
                if fore and last:
                    authors.append(f"{fore} {last}")
                elif last:
                    authors.append(last)

            journal = article_elem.findtext(".//Journal/Title", "N/A")
            year = article_elem.findtext(".//Journal/JournalIssue/PubDate/Year", "N/A")

            articles.append({
                "title": title,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "snippet": abstract[:500] + "..." if len(abstract) > 500 else abstract,
                "source": "PubMed",
                "authors": ", ".join(authors[:3]) + ("..." if len(authors) > 3 else ""),
                "publication_year": year,
                "journal": journal
            })

        return articles

    def to_documents(self, results: List[Dict[str, Any]]) -> List[Document]:
        docs = []
        for r in results:
            if "error" not in r:
                docs.append(Document(
                    page_content=f"Title: {r['title']}\n\nAbstract: {r['snippet']}",
                    metadata={
                        "source": r["url"],
                        "authors": r.get("authors", ""),
                        "year": r.get("publication_year", ""),
                        "journal": r.get("journal", "")
                    }
                ))
        return docs

@tool
def search_pubmed(query: str) -> str:
    """Search PubMed for medical research articles.
    
    Args:
        query: Medical search query
        
    Returns:
        String with formatted search results
    """
    service = PubMedService()
    results = service.search(query)
    
    if not results:
        return "No PubMed results found."
    
    if "error" in results[0]:
        return f"Error: {results[0]['error']}"
    
    output = []
    for i, r in enumerate(results, 1):
        output.append(f"{i}. {r['title']}")
        output.append(f"   Authors: {r.get('authors', 'N/A')}")
        output.append(f"   Journal: {r.get('journal', 'N/A')} ({r.get('publication_year', 'N/A')})")
        output.append(f"   URL: {r['url']}")
        output.append(f"   Abstract: {r['snippet'][:300]}...")
        output.append("")
    
    return "\n".join(output)
