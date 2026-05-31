import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnStats:
    name: str
    dtype: str
    count: int
    nulls: int
    unique: int
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None


def load_csv(path: str, delimiter: str = ",") -> pd.DataFrame:
    return pd.read_csv(path, delimiter=delimiter)


def column_stats(df: pd.DataFrame) -> list[ColumnStats]:
    stats = []
    for col in df.columns:
        series = df[col]
        s = ColumnStats(
            name=col,
            dtype=str(series.dtype),
            count=int(series.count()),
            nulls=int(series.isna().sum()),
            unique=int(series.nunique()),
        )
        if pd.api.types.is_numeric_dtype(series):
            s.min = round(float(series.min()), 4)
            s.max = round(float(series.max()), 4)
            s.mean = round(float(series.mean()), 4)
            s.median = round(float(series.median()), 4)
            s.std = round(float(series.std()), 4)
        stats.append(s)
    return stats


def filter_df(df: pd.DataFrame, query: str) -> pd.DataFrame:
    return df.query(query)


def group_summary(df: pd.DataFrame, group_col: str, agg_col: str, func: str = "sum") -> pd.DataFrame:
    valid = {"sum", "mean", "count", "max", "min"}
    if func not in valid:
        raise ValueError(f"Unsupported aggregation '{func}'. Choose from: {sorted(valid)}")
    return (
        df.groupby(group_col)[agg_col]
        .agg(func)
        .reset_index()
        .sort_values(agg_col, ascending=False)
    )


def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.duplicated()]


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        raise ValueError("No numeric columns found for correlation")
    return numeric.corr().round(3)
