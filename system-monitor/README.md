# System Monitor

A real-time terminal dashboard showing CPU, memory, disk, network, and top processes — updated live every 2 seconds.

## Features

- Live CPU usage per core with color-coded bar charts
- RAM and swap usage
- Network throughput (bytes sent/received per second)
- Disk usage across all mount points
- Top 8 processes by CPU consumption
- Configurable refresh interval

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Default: refresh every 2 seconds
python -m monitor.cli

# Faster refresh
python -m monitor.cli --interval 1

# Slower refresh
python -m monitor.cli --interval 5
```

Press `Ctrl+C` to exit.

## Run tests

```bash
pytest tests/ -v
```

## Stack

- **psutil** — cross-platform system metrics
- **Rich** — live terminal layouts (panels, tables, bars)
- **Click** — CLI interface
