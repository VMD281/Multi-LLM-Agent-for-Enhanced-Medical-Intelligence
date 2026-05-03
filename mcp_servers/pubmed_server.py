# mcp_servers/pubmed_server.py
from fastapi import FastAPI, Request
import requests

app = FastAPI()

@app.post("/pubmed_search")
async def pubmed_search(request: Request):
    data = await request.json()
    query = data.get("query")

    esearch = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": 5
        }
    ).json()

    ids = ",".join(esearch["esearchresult"]["idlist"])

    efetch = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ids,
            "retmode": "xml"
        }
    )
    
    return {"results": efetch.text}
