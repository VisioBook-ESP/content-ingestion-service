import re
from typing import Optional


class MetadataExtractor:
    LANGUAGE_INDICATORS = {
        "fr": ["le", "la", "les", "de", "du", "des", "et", "est", "que", "qui", "dans", "pour", "avec"],
        "en": ["the", "a", "an", "is", "are", "was", "were", "have", "has", "with", "for", "and", "that"],
        "es": ["el", "la", "los", "las", "de", "del", "que", "es", "en", "con", "para", "por"],
        "de": ["der", "die", "das", "und", "ist", "ein", "eine", "mit", "für", "auf", "nicht"],
    }

    def enrich(self, metadata: dict, text: str) -> dict:
        metadata["wordCount"] = self._count_words(text)
        metadata["charCount"] = len(text)

        if not metadata.get("language"):
            metadata["language"] = self._detect_language(text)

        if not metadata.get("customFields"):
            metadata["customFields"] = {}

        metadata["customFields"]["paragraphCount"] = self._count_paragraphs(text)
        metadata["customFields"]["sentenceCount"] = self._count_sentences(text)

        return metadata

    def _count_words(self, text: str) -> int:
        words = re.findall(r"\b\w+\b", text)
        return len(words)

    def _count_paragraphs(self, text: str) -> int:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return len(paragraphs)

    def _count_sentences(self, text: str) -> int:
        sentences = re.split(r"[.!?]+", text)
        return len([s for s in sentences if s.strip()])

    def _detect_language(self, text: str) -> str:
        text_lower = text.lower()
        words = set(re.findall(r"\b\w+\b", text_lower))

        scores = {}
        for lang, indicators in self.LANGUAGE_INDICATORS.items():
            score = sum(1 for word in indicators if word in words)
            scores[lang] = score

        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] >= 3:
                return detected

        return "fr"