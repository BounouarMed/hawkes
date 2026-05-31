import os
import pytest
import tempfile
import pandas as pd
from csvq.analyzer import (
    load_csv, column_stats, filter_df,
    group_summary, detect_duplicates, correlation_matrix,
)

CSV_DATA = (
    "name,age,salary,department\n"
    "Alice,30,70000,Engineering\n"
    "Bob,25,50000,Marketing\n"
    "Carol,35,90000,Engineering\n"
    "Alice,30,70000,Engineering\n"  # duplicate of row 1
)


@pytest.fixture
def sample_csv(tmp_path):
    f = tmp_path / "sample.csv"
    f.write_text(CSV_DATA)
    return str(f)


def test_load_csv(sample_csv):
    df = load_csv(sample_csv)
    assert len(df) == 4
    assert list(df.columns) == ["name", "age", "salary", "department"]


def test_column_stats_numeric(sample_csv):
    df = load_csv(sample_csv)
    stats = {s.name: s for s in column_stats(df)}
    assert stats["salary"].mean == 70000.0
    assert stats["salary"].min == 50000.0
    assert stats["salary"].max == 90000.0
    assert stats["salary"].nulls == 0


def test_column_stats_string(sample_csv):
    df = load_csv(sample_csv)
    stats = {s.name: s for s in column_stats(df)}
    assert stats["name"].mean is None
    assert stats["name"].unique == 3


def test_filter_df(sample_csv):
    df = load_csv(sample_csv)
    result = filter_df(df, "age > 28")
    assert len(result) == 3


def test_filter_df_string(sample_csv):
    df = load_csv(sample_csv)
    result = filter_df(df, "department == 'Marketing'")
    assert len(result) == 1
    assert result.iloc[0]["name"] == "Bob"


def test_group_summary_mean(sample_csv):
    df = load_csv(sample_csv)
    result = group_summary(df, "department", "salary", "mean")
    eng = result[result["department"] == "Engineering"]["salary"].values[0]
    assert eng == 70000.0  # (70000 + 90000 + 70000) / 3


def test_group_summary_invalid_func(sample_csv):
    df = load_csv(sample_csv)
    with pytest.raises(ValueError, match="Unsupported"):
        group_summary(df, "department", "salary", "variance")


def test_detect_duplicates(sample_csv):
    df = load_csv(sample_csv)
    dups = detect_duplicates(df)
    assert len(dups) == 1
    assert dups.iloc[0]["name"] == "Alice"


def test_no_duplicates():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert detect_duplicates(df).empty


def test_correlation_matrix(sample_csv):
    df = load_csv(sample_csv)
    corr = correlation_matrix(df)
    assert "age" in corr.columns
    assert "salary" in corr.columns
    assert corr.loc["age", "age"] == 1.0


def test_correlation_no_numeric():
    df = pd.DataFrame({"name": ["a", "b"], "city": ["x", "y"]})
    with pytest.raises(ValueError, match="No numeric"):
        correlation_matrix(df)
