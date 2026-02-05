import re
import unicodedata
from typing import List, Tuple


class TextCleaningService:
    QUOTE_MAPPING = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00ab": '"',
        "\u00bb": '"',
        "\u2039": "'",
        "\u203a": "'",
    }

    HEADER_PATTERNS = [
        r"^Page\s+\d+\s*(of\s+\d+)?.*$",
        r"^[-_=]{3,}$",
        r"^\s*CONFIDENTIAL\s*$",
        r"^\s*DRAFT\s*$",
    ]

    FOOTER_PATTERNS = [
        r"^Page\s+\d+\s*$",
        r"^\d+\s*$",
        r"^[-_=]{3,}$",
        r"^\s*©.*$",
        r"^\s*Copyright.*$",
    ]

    def clean(self, text: str, options) -> Tuple[str, List[str]]:
        changes = []

        if options.fixEncoding:
            text = self._fix_encoding(text)
            changes.append("fixEncoding")

        if options.normalizeQuotes:
            text = self._normalize_quotes(text)
            changes.append("normalizeQuotes")

        if options.removeHeaders:
            text = self._remove_headers(text)
            changes.append("removeHeaders")

        if options.removeFooters:
            text = self._remove_footers(text)
            changes.append("removeFooters")

        if options.removeExtraSpaces:
            text = self._remove_extra_spaces(text)
            changes.append("removeExtraSpaces")

        return text, changes

    def _fix_encoding(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        return text

    def _normalize_quotes(self, text: str) -> str:
        for fancy, simple in self.QUOTE_MAPPING.items():
            text = text.replace(fancy, simple)
        return text

    def _remove_extra_spaces(self, text: str) -> str:
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            cleaned_line = " ".join(line.split())
            cleaned_lines.append(cleaned_line)
        text = "\n".join(cleaned_lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _remove_headers(self, text: str) -> str:
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            is_header = any(
                re.match(pattern, line.strip(), re.IGNORECASE)
                for pattern in self.HEADER_PATTERNS
            )
            if not is_header:
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def _remove_footers(self, text: str) -> str:
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            is_footer = any(
                re.match(pattern, line.strip(), re.IGNORECASE)
                for pattern in self.FOOTER_PATTERNS
            )
            if not is_footer:
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines)