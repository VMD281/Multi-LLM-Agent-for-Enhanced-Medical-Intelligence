import requests

def ask_llm(prompt, model="mistral"):
    print(f"(Ollama - {model}) Generating answer...")
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"].strip()
