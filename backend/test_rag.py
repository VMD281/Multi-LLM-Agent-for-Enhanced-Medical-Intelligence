"""
Test the RAG system - Build index and perform sample searches.
"""

from app.rag import build_rag

def main():
    """Build RAG and test with sample queries"""
    
    print("\nTESTING MEDICAL RAG SYSTEM\n")
    
    # Build RAG
    vector_store = build_rag()
    
    if vector_store is None:
        print("Failed to build RAG")
        return
    
    # Test queries
    test_queries = [
        "What is hypertension management?",
        "How to treat heart failure?",
        "Acute coronary syndrome treatment",
        "Atrial fibrillation anticoagulation",
        "Stroke prevention guidelines",
    ]
    
    print("\n" + "="*70)
    print("🔍 TESTING SEMANTIC SEARCH")
    print("="*70)
    
    for query in test_queries:
        print(f"\n📌 Query: {query}")
        results = vector_store.search(query, k=2)
        
        if results:
            for result in results:
                print(f"       Category: {result['category']}")
                snippet = result['content'][:100].replace('\n', ' ')
                print(f"       Preview: {snippet}...")
        else:
            print("   ❌ No results found")
    
    print("\n" + "="*70)
    print("✨ RAG SYSTEM TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()