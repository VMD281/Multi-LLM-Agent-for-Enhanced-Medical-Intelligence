# mcp_clients/pubmed_client.py
import requests

# def query_pubmed(query):
#     response = requests.post("http://localhost:8001/pubmed_search", json={"query": query})
#     return response.json()
def query_pubmed(query):
    print(f"(Mock) Querying PubMed for: {query}")
    return {
        "results": [
            {
                "title": "Early Symptoms and Diagnosis of Diabetes",
                "snippet": "Fatigue, frequent urination, and blurred vision are common early indicators of diabetes."
            }
        ]
    }
