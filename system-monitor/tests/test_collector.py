import pytest
from monitor.collector import snapshot
from monitor.dashboard import _bar, _human


def test_snapshot_cpu_range():
    snap = snapshot()
    assert 0.0 <= snap.cpu_percent <= 100.0
    assert all(0.0 <= c <= 100.0 for c in snap.cpu_per_core)


def test_snapshot_memory_sane():
    snap = snapshot()
    assert snap.memory_total > 0
    assert 0 <= snap.memory_used <= snap.memory_total
    assert 0.0 <= snap.memory_percent <= 100.0


def test_snapshot_disk_present():
    snap = snapshot()
    assert isinstance(snap.disk_usage, dict)


def test_snapshot_net_nonnegative():
    snap = snapshot(prev_net_sent=0, prev_net_recv=0)
    assert snap.net_bytes_sent >= 0
    assert snap.net_bytes_recv >= 0


def test_snapshot_top_processes():
    snap = snapshot()
    assert isinstance(snap.top_processes, list)
    assert len(snap.top_processes) <= 8


def test_bar_empty():
    assert "░" in _bar(0)


def test_bar_full():
    result = _bar(100)
    assert "█" in result
    assert "red" in result


def test_bar_warning():
    result = _bar(80)
    assert "yellow" in result


def test_human_bytes():
    assert _human(500) == "500.0 B"
    assert _human(1024) == "1.0 KB"
    assert _human(1024 * 1024) == "1.0 MB"
