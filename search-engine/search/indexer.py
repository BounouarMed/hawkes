import re
import math
from collections import defaultdict
from dataclasses import dataclass, field

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "is", "it", "this", "that", "was", "are", "be", "as", "by",
    "from", "with", "not", "have", "has", "had", "will", "would", "can",
    "could", "do", "does", "did", "its", "are", "been", "being",
}


@dataclass
class Document:
    id: int
    title: str
    content: str
    tokens: list[str] = field(default_factory=list)


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\b[a-z][a-z0-9]*\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class InvertedIndex:
    def __init__(self):
        self.docs: dict[int, Document] = {}
        self.index: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._next_id: int = 0

    def add(self, title: str, content: str) -> int:
        doc_id = self._next_id
        self._next_id += 1
        tokens = tokenize(title + " " + content)
        doc = Document(id=doc_id, title=title, content=content, tokens=tokens)
        self.docs[doc_id] = doc
        for token in tokens:
            self.index[token][doc_id] += 1
        return doc_id

    def search(self, query: str, top_k: int = 10) -> list[tuple[float, Document]]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        candidates: set[int] = set()
        for token in query_tokens:
            candidates.update(self.index.get(token, {}).keys())

        if not candidates:
            return []

        N = len(self.docs)
        scores: dict[int, float] = {}
        for token in query_tokens:
            if token not in self.index:
                continue
            df = len(self.index[token])
            idf = math.log((N + 1) / (df + 1)) + 1.0
            for doc_id in candidates:
                tf = self.index[token].get(doc_id, 0)
                if tf > 0:
                    tf_norm = 1.0 + math.log(tf)
                    scores[doc_id] = scores.get(doc_id, 0.0) + tf_norm * idf

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(score, self.docs[doc_id]) for doc_id, score in ranked]

    def __len__(self) -> int:
        return len(self.docs)
