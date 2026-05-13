"""
Generate embeddings for medical documents using sentence-transformers.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings

class MedicalEmbeddings(HuggingFaceEmbeddings):
    """Generate embeddings for medical text - inherits from HuggingFaceEmbeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"\n Loading embedding model: {model_name}")
        print("   (This may take 1-2 minutes on first run)...")
        
        # Initialize parent class
        super().__init__(
            model_name=model_name,
            model_kwargs={"device": "cpu"}
        )
        
        print("Embeddings ready!")