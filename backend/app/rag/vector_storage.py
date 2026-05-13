"""
FAISS vector store for medical document retrieval.
"""

import os
from typing import List, Dict, Any
from langchain.schema import Document
from langchain.vectorstores import FAISS

class MedicalVectorStore:
    """FAISS vector store for RAG"""
    
    def __init__(
        self,
        embeddings,
        index_path: str = "data/faiss_index"
    ):
        self.embeddings = embeddings
        self.index_path = index_path
        self.vector_store = None
        
        # Load existing index if it exists
        if os.path.exists(index_path):
            print(f"\n📂 Loading existing FAISS index from {index_path}...")
            try:
                self.vector_store = FAISS.load_local(index_path, embeddings)
                print("   ✅ Index loaded!")
            except Exception as e:
                print(f"   ⚠️ Could not load existing index: {e}")
        else:
            print(f"\n📂 No existing FAISS index at {index_path}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to vector store"""
        
        print(f"\n🔧 Adding {len(documents)} chunks to FAISS...")
        
        if self.vector_store is None:
            # Create new index
            print("   Creating new FAISS index...")
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            # Add to existing index
            print("   Adding to existing FAISS index...")
            self.vector_store.add_documents(documents)
        
        # Save index
        self._save_index()
        print("   ✅ Documents indexed!")
    
    def _save_index(self) -> None:
        """Save FAISS index to disk"""
        
        print(f"\n💾 Saving FAISS index to {self.index_path}...")
        
        os.makedirs(self.index_path, exist_ok=True)
        self.vector_store.save_local(self.index_path)
        
        print("   ✅ Index saved!")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        
        if self.vector_store is None:
            print("⚠️ Vector store is empty!")
            return []
        
        print(f"\n🔍 Searching: '{query}'")
        
        # Similarity search with scores
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            print(f"Search error: {e}")
            return []
        
        formatted_results = []
        for i, (doc, score) in enumerate(results, 1):
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get('source', 'Unknown'),
                "category": doc.metadata.get('category', 'Unknown'),
                "score": float(score)
            })
            print(f"   [{i}] Score: {score:.3f} | {doc.metadata.get('source', 'Unknown')}")
        
        return formatted_results
    
    def get_retriever(self, k: int = 5):
        """Get LangChain retriever"""
        if self.vector_store is None:
            return None
        return self.vector_store.as_retriever(search_kwargs={"k": k})