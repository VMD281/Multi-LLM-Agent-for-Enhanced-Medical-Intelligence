from mcp_clients.web_search_client import query_web_search
from mcp_clients.pubmed_client import query_pubmed
from mcp_clients.llm_client import ask_llm

def synthesize_answer(user_query, web_results, pubmed_results):
    web_text = "\n".join([f"{r['title']}: {r['snippet']}" for r in web_results["results"]])
    pubmed_text = "\n".join([f"{r['title']}: {r['snippet']}" for r in pubmed_results["results"]])

    prompt = f"""
You are a medical assistant. Based on the user query: "{user_query}",
analyze the following:

-- Web Search Results --
{web_text}

-- PubMed Abstracts --
{pubmed_text}

Give a concise, accurate, medically reliable response.
"""
    return ask_llm(prompt)

def main():
    query = input("Enter your medical query: ")
    web_results = query_web_search(query)
    pubmed_results = query_pubmed(query)
    final_answer = synthesize_answer(query, web_results, pubmed_results)
    print("\n📘 Answer:\n", final_answer)

if __name__ == "__main__":
    main()
