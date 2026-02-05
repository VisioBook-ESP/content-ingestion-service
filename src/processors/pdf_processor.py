from src.processors.base import BaseProcessor


class PDFProcessor(BaseProcessor):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".pdf")

    def extract_text(self, file_path: str) -> str:
        return "Texte extrait du PDF"

    def extract_metadata(self, file_path: str) -> dict:
        return {"title": None, "author": None, "pages": None}
