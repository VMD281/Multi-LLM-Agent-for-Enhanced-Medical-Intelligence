import os
from dotenv import load_dotenv
from src.agents.orchestrator import MedicalAgentOrchestrator

load_dotenv()

def check_api_keys():
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.getenv("NCBI_API_KEY"):
        missing.append("NCBI_API_KEY")
    if not os.getenv("BRAVE_SEARCH_API_KEY"):
        print("[WARNING] BRAVE_SEARCH_API_KEY not set - web search will be disabled")
    
    if missing:
        print(f"\n[ERROR] Missing required API keys: {', '.join(missing)}")
        print("Please set these environment variables in your .env file:")
        print("  ANTHROPIC_API_KEY=your_anthropic_key")
        print("  NCBI_API_KEY=your_ncbi_key")
        print("  BRAVE_SEARCH_API_KEY=your_brave_key (optional)")
        return False
    return True


def main():
    print("=" * 60)
    print("  Multi-Agent Medical Intelligence System")
    print("  Powered by LangChain, LangGraph & Claude LLM")
    print("=" * 60)
    
    if not check_api_keys():
        return
    
    print("\nInitializing medical agent orchestrator...")
    orchestrator = MedicalAgentOrchestrator()
    print("Ready! Type 'quit' or 'exit' to end.\n")
    
    while True:
        try:
            query = input("\n[You] Ask a medical question: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            print("\n" + "-" * 50)
            print("Processing with multi-agent workflow...")
            print("-" * 50)
            
            result = orchestrator.run(query)
            
            print("\n" + "=" * 60)
            print("MEDICAL INTELLIGENCE REPORT")
            print("=" * 60)
            
            print(f"\n[Query]: {result['query']}")
            
            if result.get("pubmed_results"):
                print(f"\n[PubMed Sources]: {len(result['pubmed_results'])} articles found")
                for i, article in enumerate(result["pubmed_results"][:3], 1):
                    if isinstance(article, dict) and "error" not in article:
                        print(f"  {i}. {article.get('title', 'N/A')[:60]}...")
            
            if result.get("web_results"):
                print(f"\n[Web Sources]: {len(result['web_results'])} results found")
                for i, web in enumerate(result["web_results"][:3], 1):
                    if isinstance(web, dict) and "error" not in web:
                        print(f"  {i}. {web.get('title', 'N/A')[:60]}...")
            
            print("\n" + "-" * 60)
            print("[Synthesized Answer]")
            print("-" * 60)
            print(result.get("answer", "Unable to generate answer"))
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    main()
