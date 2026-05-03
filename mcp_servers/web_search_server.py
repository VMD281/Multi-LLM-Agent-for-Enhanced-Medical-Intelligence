from fastapi import FastAPI, Request
import requests

app = FastAPI()
@app.post("/web_search")
async def search(request : Request):
    data = await request.json()
    query = data.get("query")

    headers = {
        "X_API_KEY": "d4d7efbab8f27cd5fb6fb5527ad9e47b195d02a1"
    }

    params = {
        "q": query
    }
    response = requests.get("https://google.serper.dev/search", url, headers=headers, params=params)
    return response.json()