"""Local extractive summary used when no LLM backend is configured."""
from __future__ import annotations

import re
from collections import Counter

from .search import tokens


def extractive_summary(value: str, count: int = 3) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", value) if s.strip()]
    if not sentences:
        return ""
    stop = {"the", "a", "and", "is", "to", "of", "in", "for", "we"}
    frequencies = Counter(word for word in tokens(value) if word not in stop)
    ranked = sorted(
        range(len(sentences)),
        key=lambda i: (
            -sum(frequencies[w] for w in tokens(sentences[i]))
            / max(1, len(tokens(sentences[i]))),
            i,
        ),
    )[:count]
    return " ".join(sentences[i] for i in sorted(ranked))
