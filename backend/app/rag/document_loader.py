from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


class CardiovascularDocumentLoader:
    """Load cardiovascular medical PDFs stored with the RAG package."""

    def __init__(self, documents_dir: str | Path = None):
        self.documents_dir = (
            Path(documents_dir).resolve()
            if documents_dir
            else Path(__file__).parent.resolve()
        )
        print(f"✅ Document loader initialized at: {self.documents_dir}")

    def load_all_documents(self) -> List[Document]:
        pdf_paths = sorted(self.documents_dir.glob("*.pdf"))

        if not pdf_paths:
            print("⚠️ No PDF documents were found in the RAG documents directory.")
            return []

        documents: List[Document] = []
        for path in pdf_paths:
            print(f"📄 Loading PDF: {path.name}")
            loader = PyPDFLoader(str(path))
            pages = loader.load()
            for page in pages:
                page.metadata["source"] = path.name
                page.metadata.setdefault("category", self._guess_category(path.name))
                documents.append(page)

        print(f"✅ Loaded {len(documents)} document chunks from {len(pdf_paths)} PDF(s)")
        return documents

    @staticmethod
    def _guess_category(filename: str) -> str:
        lower = filename.lower()
        if "hypertension" in lower or "jmc7" in lower:
            return "Hypertension"
        if "cholesterol" in lower or "atp3" in lower:
            return "Cholesterol"
        if "statins" in lower:
            return "Statin therapy"
        if "heart" in lower or "ocr" in lower:
            return "Cardiovascular disease"
        if "stroke" in lower:
            return "Stroke prevention"
        return "Cardiovascular"
