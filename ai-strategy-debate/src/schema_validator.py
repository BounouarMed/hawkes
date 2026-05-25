import json
from pathlib import Path
import jsonschema

SCHEMA_DIR = Path("schemas")
_cache: dict[str, dict] = {}

class ValidationError(Exception):
    pass

def _load(name: str) -> dict:
    if name not in _cache:
        candidates = list(SCHEMA_DIR.glob(f"{name}*.json"))
        if not candidates:
            return {"type": "object"}
        _cache[name] = json.loads(candidates[0].read_text())
    return _cache[name]

def validate(data: dict, schema_name: str) -> None:
    try:
        jsonschema.validate(instance=data, schema=_load(schema_name))
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Schema '{schema_name}' failed: {e.message}") from e

def is_valid(data: dict, schema_name: str) -> bool:
    try:
        validate(data, schema_name)
        return True
    except ValidationError:
        return False
