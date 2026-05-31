import pytest
from search.indexer import InvertedIndex, tokenize


def test_tokenize_lowercases():
    assert "hello" in tokenize("Hello World")
    assert "Hello" not in tokenize("Hello World")


def test_tokenize_removes_stopwords():
    tokens = tokenize("the quick brown fox")
    assert "the" not in tokens
    assert "quick" in tokens
    assert "brown" in tokens


def test_tokenize_removes_single_chars():
    tokens = tokenize("I go to a big store")
    assert "I" not in tokens
    assert "a" not in tokens
    assert "go" in tokens
    assert "big" in tokens


def test_add_and_basic_search():
    idx = InvertedIndex()
    idx.add("Python Tutorial", "Learn Python programming from scratch")
    idx.add("Java Guide", "Java is an object-oriented programming language")
    idx.add("Cooking Basics", "How to cook pasta and Italian dishes")

    results = idx.search("Python programming")
    assert len(results) > 0
    assert results[0][1].title == "Python Tutorial"


def test_tf_ranking_prefers_higher_frequency():
    idx = InvertedIndex()
    idx.add("Python Deep Dive", "python python python advanced python techniques")
    idx.add("Multi Language", "python and java and ruby and go")

    results = idx.search("python")
    assert results[0][1].title == "Python Deep Dive"


def test_idf_penalizes_common_terms():
    idx = InvertedIndex()
    for i in range(10):
        idx.add(f"Doc {i}", "common word appears here in every document")
    idx.add("Special", "rare unique term never seen before")

    results = idx.search("rare")
    assert len(results) == 1
    assert results[0][1].title == "Special"


def test_search_no_results():
    idx = InvertedIndex()
    idx.add("Test", "some content here")
    assert idx.search("zzzyyyxxx") == []


def test_search_empty_query():
    idx = InvertedIndex()
    idx.add("Doc", "content")
    assert idx.search("") == []


def test_search_stopwords_only():
    idx = InvertedIndex()
    idx.add("Doc", "content")
    assert idx.search("the and or") == []


def test_index_length():
    idx = InvertedIndex()
    idx.add("A", "alpha")
    idx.add("B", "beta")
    idx.add("C", "gamma")
    assert len(idx) == 3


def test_multi_term_query_union():
    idx = InvertedIndex()
    idx.add("Python Doc", "python only")
    idx.add("Java Doc", "java only")
    idx.add("Both", "python and java together")

    results = idx.search("python java")
    titles = [r[1].title for r in results]
    assert "Both" in titles
    assert "Python Doc" in titles
    assert "Java Doc" in titles
