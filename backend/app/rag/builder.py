"""
Build and manage the RAG system.
"""

import time
from typing import List
from langchain_core.documents import Document
from .document_loader import CardiovascularDocumentLoader
from .text_splitter import MedicalTextSplitter
from .embeddings import MedicalEmbeddings
from .vector_store import MedicalVectorStore

class RAGBuilder:
    """Build complete RAG pipeline"""
    
    def __init__(self):
        self.documents = None
        self.chunks = None
        self.embeddings = None
        self.vector_store = None
    
    def build_rag_pipeline(self, rebuild: bool = False) -> MedicalVectorStore:
        """
        Build complete RAG pipeline.
        
        Args:
            rebuild: Force rebuild even if FAISS index exists
        
        Returns:
            Configured MedicalVectorStore
        """
        
        print("\n" + "="*70)
        print(" BUILDING MEDICAL RAG SYSTEM")
        print("="*70)
        
        start_time = time.time()
        
        # Step 1: Initialize embeddings
        print("\n[1/5] Initializing embeddings...")
        self.embeddings = MedicalEmbeddings()
        
        # Step 2: Initialize vector store
        print("\n[2/5] Initializing FAISS vector store...")
        self.vector_store = MedicalVectorStore(self.embeddings)
        
        # Check if we need to rebuild
        if rebuild or self.vector_store.vector_store is None:
            # Step 3: Load documents
            print("\n[3/5] Loading documents...")
            loader = CardiovascularDocumentLoader()
            self.documents = loader.load_all_documents()
            
            if not self.documents:
                print(" No documents found!")
                return None
            
            # Step 4: Split documents
            print("\n[4/5] Splitting documents into chunks...")
            splitter = MedicalTextSplitter(chunk_size=512, chunk_overlap=100)
            self.chunks = splitter.split_documents(self.documents)
            
            # Step 5: Index documents
            print("\n[5/5] Indexing documents to FAISS...")
            self.vector_store.add_documents(self.chunks)
        else:
            print("\n[3-5/5] Using existing FAISS index ✅")
        
        # Summary
        elapsed_time = time.time() - start_time
        print("\n" + "="*70)
        print("✨ RAG SYSTEM READY")
        print("="*70)
        print(f" Build time: {elapsed_time:.2f} seconds")
        print(f" Indexed documents available for semantic search")
        print("="*70)
        
        return self.vector_store


def build_rag():
    """Convenience function to build RAG"""
    builder = RAGBuilder()
    return builder.build_rag_pipeline()