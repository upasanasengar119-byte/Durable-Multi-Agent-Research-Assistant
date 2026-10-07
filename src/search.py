"""Sparse TF-IDF cosine retrieval (no neural embeddings required)."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter


def tokens(value: str) -> list[str]:
    return re.findall(r"[\w]+", unicodedata.normalize("NFC", value).casefold())


class Search:
    """Exact TF-IDF cosine search over a small local corpus."""

    def __init__(self, documents: list[dict]):
        self.docs = documents
        frequencies: Counter[str] = Counter()
        for doc in documents:
            frequencies.update(set(tokens(doc["text"])))
        n = len(documents)
        self.idf = {w: math.log((1 + n) / (1 + count)) + 1 for w, count in frequencies.items()}
        self.vectors = [self.vector(doc["text"]) for doc in documents]

    def vector(self, value: str) -> dict[str, float]:
        counts = Counter(tokens(value))
        return {
            word: (1 + math.log(count)) * self.idf[word]
            for word, count in counts.items()
            if word in self.idf
        }

    def query(self, value: str, k: int = 3) -> list[dict]:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("query must be a nonempty string")
        query_vec = self.vector(value)
        scored = []
        for index, doc_vec in enumerate(self.vectors):
            scored.append((self._cosine(query_vec, doc_vec), index))
        ranked = sorted(scored, key=lambda pair: (-pair[0], pair[1]))
        return [
            dict(self.docs[index], score=round(score, 6))
            for score, index in ranked[:k]
            if score > 0
        ]

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        denom = math.sqrt(sum(v * v for v in left.values()))
        denom *= math.sqrt(sum(v * v for v in right.values()))
        if not denom:
            return 0.0
        return sum(value * right.get(key, 0.0) for key, value in left.items()) / denom
