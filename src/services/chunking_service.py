class ChunkingService:
    def chunk(self, text: str, size: int, overlap: int):
        words = text.split()
        if not words:
            return [""]
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i : i + size]
            chunks.append(" ".join(chunk_words))
            i += size - overlap
        return chunks
