import fnmatch
import json
import logging
from pathlib import Path

logger = logging.getLogger("ledger")

class SessionLedger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.root = Path("sessions") / session_id
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "__").replace(" ", "_")
        return self.root / f"{safe}.json"

    def write(self, key: str, data: dict) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.debug("Ledger write: %s", key)

    def read(self, key: str) -> dict | None:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError as e:
            logger.error("Ledger read error %s: %s", key, e)
            return None

    def read_pattern(self, pattern: str) -> list[dict]:
        safe_pattern = pattern.replace("/", "__") + ".json"
        results = []
        for p in sorted(self.root.glob("*.json")):
            if fnmatch.fnmatch(p.name, safe_pattern):
                try:
                    results.append(json.loads(p.read_text()))
                except json.JSONDecodeError:
                    pass
        return results

    def read_all(self) -> dict:
        result = {}
        for p in sorted(self.root.glob("*.json")):
            key = p.stem.replace("__", "/")
            try:
                result[key] = json.loads(p.read_text())
            except json.JSONDecodeError:
                pass
        return result

    def finalise(self, cost_summary: dict) -> None:
        self.write("cost_summary", cost_summary)
