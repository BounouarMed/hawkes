import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("provenance")

class ProvenanceLog:
    def __init__(self, session_id: str):
        audit_dir = Path("audits")
        audit_dir.mkdir(exist_ok=True)
        self._path = audit_dir / f"{session_id}.jsonl"

    def record(self, event_type: str, agent: str, payload: dict) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "agent": agent,
            "payload": payload,
        }
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.error("Provenance write failed: %s", e)
