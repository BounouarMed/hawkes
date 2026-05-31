# Mini Search Engine

A full-text search engine built from scratch in Python — inverted index, TF-IDF ranking, persistent JSON store, and a terminal CLI.

## How it works

1. **Tokenization** — lowercases text, removes stopwords and single-character tokens
2. **Inverted index** — maps each term to the set of documents containing it + term frequency
3. **TF-IDF ranking** — scores candidates with log-normalized TF and smoothed IDF so rare terms outrank common ones
4. **Persistence** — the index serializes to a single JSON file for simplicity

## Install

```bash
pip install -r requirements.txt
```

## Usage

### Add individual documents
```bash
python -m search.cli add "Python Tutorial" "Learn Python programming from scratch"
python -m search.cli add "Java Guide" "Java is an object-oriented programming language"
python -m search.cli add "Cooking Basics" "How to cook pasta and Italian dishes"
```

### Bulk index from a JSON file
```bash
# docs.json: [{"title": "...", "content": "..."}, ...]
python -m search.cli index docs.json
```

### Search
```bash
python -m search.cli search "Python programming"
python -m search.cli search "Italian food" --top 3
```

### Stats and cleanup
```bash
python -m search.cli stats
python -m search.cli clear
```

## Run tests

```bash
pytest tests/ -v
```

## Stack

- Pure Python standard library (no ML dependencies)
- **Click** — CLI
- **Rich** — results table with scores
- **pytest** — algorithmic unit tests
