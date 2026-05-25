"""
Render the final debate report to reports/.
Usage: python src/render_report.py --session <id> [--escalation]
Prints: absolute path of the written report
"""
import argparse
import json
from pathlib import Path

from src.session_ledger import SessionLedger
from src.report_renderer import render_report, render_escalation_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--escalation", action="store_true")
    args = parser.parse_args()

    ledger       = SessionLedger(args.session)
    scenario     = ledger.read("scenario") or {}
    final_result = ledger.read("final_result") or {}
    cost_summary = ledger.read("cost_summary") or {}

    gates = {
        "ethics_lead":        ledger.read("ethics_lead_verdict") or {},
        "compliance_manager": ledger.read("compliance_manager_verdict") or {},
        "security_specialist":ledger.read("security_specialist_verdict") or {},
    }

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    sid = scenario.get("scenario_id", "unknown")

    if args.escalation:
        blocked = [
            (k, v) for k, v in gates.items()
            if v.get("gate_result") == "block"
            or v.get("prohibited_practice")
            or v.get("injection_detected")
        ]
        content = render_escalation_report(scenario, args.session, blocked, gates, ledger)
        path = out_dir / f"{sid}_{args.session}_ESCALATION.md"
    else:
        final_result["cost_usd"] = cost_summary.get("total_usd", 0)
        content = render_report(scenario, args.session, final_result, gates, ledger)
        path = out_dir / f"{sid}_{args.session}.md"

    path.write_text(content, encoding="utf-8")
    print(str(path.resolve()))


if __name__ == "__main__":
    main()
