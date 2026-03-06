from src.processors.base import BaseProcessor

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PDFProcessor(BaseProcessor):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".pdf")

    def extract_text(self, file_path: str) -> str:
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF is required for PDF processing. " "Install it with: pip install pymupdf"
            )

        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text.strip())
        doc.close()

        return "\n\n".join(pages)

    def extract_metadata(self, file_path: str) -> dict:
        if not PYMUPDF_AVAILABLE:
            return {"title": None, "author": None, "pages": None}

        doc = fitz.open(file_path)
        meta = doc.metadata
        page_count = doc.page_count
        doc.close()

        return {
            "title": meta.get("title") or None,
            "author": meta.get("author") or None,
            "pages": page_count,
            "created": meta.get("creationDate") or None,
            "modified": meta.get("modDate") or None,
            "subject": meta.get("subject") or None,
        }
