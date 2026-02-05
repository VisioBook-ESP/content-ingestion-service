import re
from src.processors.base import BaseProcessor

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HTMLProcessor(BaseProcessor):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith((".html", ".htm"))

    def extract_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if BS4_AVAILABLE:
            soup = BeautifulSoup(content, "html.parser")

            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()

            text = soup.get_text(separator="\n")
        else:
            text = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"&[a-zA-Z]+;", " ", text)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def extract_metadata(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = {"title": None, "author": None, "pages": None}

        if BS4_AVAILABLE:
            soup = BeautifulSoup(content, "html.parser")

            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.get_text().strip()

            author_meta = soup.find("meta", attrs={"name": "author"})
            if author_meta:
                metadata["author"] = author_meta.get("content")

            description_meta = soup.find("meta", attrs={"name": "description"})
            if description_meta:
                metadata["description"] = description_meta.get("content")
        else:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

        return metadata
