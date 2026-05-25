"""
Check gate verdicts for automatic blocks.
Usage: python src/gate_check.py --session <id>
Prints: JSON {"status": "blocked"|"clear", "blocked": [...], "warnings": [...]}
"""
import argparse
import json

from src.session_ledger import SessionLedger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    args = parser.parse_args()

    ledger = SessionLedger(args.session)
    ethics     = ledger.read("ethics_lead_verdict") or {}
    compliance = ledger.read("compliance_manager_verdict") or {}
    security   = ledger.read("security_specialist_verdict") or {}

    blocked = []
    if ethics.get("gate_result") == "block" or ethics.get("prohibited_practice"):
        blocked.append({
            "gate": "ethics_lead",
            "reason": ethics.get("issues_found", []),
            "prohibited_practice": ethics.get("prohibited_practice", False),
        })
    if compliance.get("gate_result") == "block":
        blocked.append({
            "gate": "compliance_manager",
            "reason": compliance.get("flags", []),
        })
    if security.get("gate_result") == "block" or security.get("injection_detected"):
        blocked.append({
            "gate": "security_specialist",
            "reason": security.get("threats_found", []),
            "injection_detected": security.get("injection_detected", False),
        })

    warnings = [
        name for name, v in [
            ("ethics", ethics),
            ("compliance", compliance),
            ("security", security),
        ]
        if v.get("gate_result") == "pass_with_warnings"
    ]

    print(json.dumps({
        "status": "blocked" if blocked else "clear",
        "blocked": blocked,
        "warnings": warnings,
    }))


if __name__ == "__main__":
    main()
