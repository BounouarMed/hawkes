import psutil
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemSnapshot:
    timestamp: datetime
    cpu_percent: float
    cpu_per_core: list[float]
    memory_total: int
    memory_used: int
    memory_percent: float
    swap_used: int
    swap_percent: float
    disk_usage: dict[str, tuple[int, int, float]]
    net_bytes_sent: int
    net_bytes_recv: int
    top_processes: list[tuple[str, float, float]]


def snapshot(prev_net_sent: int = 0, prev_net_recv: int = 0) -> SystemSnapshot:
    net = psutil.net_io_counters()

    disks: dict[str, tuple[int, int, float]] = {}
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks[part.mountpoint] = (usage.used, usage.total, usage.percent)
        except PermissionError:
            pass

    procs: list[tuple[str, float, float]] = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procs.append((
                p.info["name"] or "?",
                p.info["cpu_percent"] or 0.0,
                p.info["memory_percent"] or 0.0,
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    top = sorted(procs, key=lambda x: x[1], reverse=True)[:8]

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return SystemSnapshot(
        timestamp=datetime.now(),
        cpu_percent=psutil.cpu_percent(interval=None),
        cpu_per_core=psutil.cpu_percent(percpu=True),
        memory_total=mem.total,
        memory_used=mem.used,
        memory_percent=mem.percent,
        swap_used=swap.used,
        swap_percent=swap.percent,
        disk_usage=disks,
        net_bytes_sent=max(0, net.bytes_sent - prev_net_sent),
        net_bytes_recv=max(0, net.bytes_recv - prev_net_recv),
        top_processes=top,
    )
