"""
Split documents into chunks for optimal RAG retrieval.
"""

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class MedicalTextSplitter:
    """Split medical documents into chunks"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        print(f"✅ Text splitter initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        
        print(f"\n✂️ Splitting {len(documents)} document(s) into chunks...")
        
        # Split
        chunks = self.splitter.split_documents(documents)
        
        print(f"📊 Created {len(chunks)} chunks")
        print(f"   Average chunk size: {self.chunk_size} characters")
        
        return chunks