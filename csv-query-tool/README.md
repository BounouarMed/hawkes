# CSV Query Tool

Analyze and query CSV files from the terminal without writing any Python.

## Features

- **info** — overview + per-column stats (nulls, unique values, min/max/mean)
- **query** — filter rows with pandas query expressions
- **group** — group-by aggregation (sum, mean, count, max, min)
- **duplicates** — detect and display duplicate rows
- **correlate** — numeric correlation matrix with color-coded highlights

## Install

```bash
pip install -r requirements.txt
```

## Usage

### Explore a file
```bash
python -m csvq.cli info sales.csv
```

### Filter rows
```bash
# Simple condition
python -m csvq.cli query sales.csv "revenue > 10000"

# Multiple conditions
python -m csvq.cli query sales.csv "region == 'West' and revenue > 5000"

# Save filtered result
python -m csvq.cli query sales.csv "status == 'active'" --output active.csv
```

### Group and aggregate
```bash
# Total revenue by region
python -m csvq.cli group sales.csv region revenue --func sum

# Average salary by department
python -m csvq.cli group employees.csv department salary --func mean
```

### Find duplicates
```bash
python -m csvq.cli duplicates data.csv
```

### Correlation matrix
```bash
python -m csvq.cli correlate metrics.csv
```

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **pandas** — data loading, filtering, grouping, stats
- **Click** — CLI framework
- **Rich** — terminal tables with color formatting
- **pytest** — unit tests using temp CSV fixtures
