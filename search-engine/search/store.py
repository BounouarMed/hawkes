import json
from pathlib import Path
from search.indexer import InvertedIndex


def save(index: InvertedIndex, path: str) -> None:
    data = {
        "next_id": index._next_id,
        "docs": {
            str(doc_id): {"title": doc.title, "content": doc.content}
            for doc_id, doc in index.docs.items()
        },
    }
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load(path: str) -> InvertedIndex:
    data = json.loads(Path(path).read_text())
    idx = InvertedIndex()
    for doc_data in data["docs"].values():
        idx.add(doc_data["title"], doc_data["content"])
    return idx
