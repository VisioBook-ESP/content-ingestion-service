from src.processors.base import BaseProcessor


class TextProcessor(BaseProcessor):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(".txt")

    def extract_text(self, file_path: str) -> str:
        with open(file_path) as f:
            return f.read()

    def extract_metadata(self, file_path: str) -> dict:
        return {}
