"""
Initialize a debate session.
Usage: python src/session_init.py --scenario <path>
Prints: session_id to stdout
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.schema_validator import validate, ValidationError
from src.session_ledger import SessionLedger
from src.provenance import ProvenanceLog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()

    with open(args.scenario, encoding="utf-8") as f:
        scenario = yaml.safe_load(f)

    try:
        validate(scenario, "scenario")
    except ValidationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    session_id = f"{scenario['scenario_id']}_{ts}"

    ledger = SessionLedger(session_id)
    ledger.write("scenario", scenario)

    prov = ProvenanceLog(session_id)
    prov.record("session_start", "orchestrator", {
        "scenario_id": scenario["scenario_id"],
        "session_id": session_id,
        "scenario_path": args.scenario,
        "project_root": str(Path.cwd()),
    })

    print(session_id)


if __name__ == "__main__":
    main()
