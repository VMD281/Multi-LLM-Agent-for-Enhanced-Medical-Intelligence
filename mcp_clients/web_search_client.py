# mcp_clients/web_search_client.py

# def query_web_search(query):
#     response = requests.post("http://localhost:8000/web_search", json={"query": query})
#     return response.json()

from duckduckgo_search import ddg

def query_web_search(query):
    print(f"(DuckDuckGo) Querying web for: {query}")
    results = ddg(query, max_results=5)
    if not results:
        return {"results": []}
    return {
        "results": [{"title": r["title"], "snippet": r["body"]} for r in results]
    }
