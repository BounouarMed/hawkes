"""
Main orchestrator — called by Claude Code via Bash tool.
python src/orchestrator.py --scenario data/scenarios/<name>.yaml
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.schema_validator import validate, ValidationError
from src.cost_tracker import CostTracker
from src.session_ledger import SessionLedger
from src.provenance import ProvenanceLog
from src.router import Router
from src.debate_loop import DebateLoop
from src.report_renderer import render_report, render_escalation_report

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("orchestrator")
MAX_ROUNDS = int(os.getenv("MAX_DEBATE_ROUNDS", "3"))


def load_scenario(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    validate(data, "scenario")
    return data


def session_id(scenario_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{scenario_id}_{ts}"


def save_report(scenario_id: str, sid: str, content: str, escalation: bool = False) -> Path:
    out = Path("reports")
    out.mkdir(exist_ok=True)
    suffix = "_ESCALATION" if escalation else ""
    p = out / f"{scenario_id}_{sid}{suffix}.md"
    p.write_text(content, encoding="utf-8")
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()

    scenario = load_scenario(args.scenario)
    sid = session_id(scenario["scenario_id"])

    ledger   = SessionLedger(sid)
    prov     = ProvenanceLog(sid)
    cost     = CostTracker()
    router   = Router(scenario, ledger)
    loop     = DebateLoop(scenario, sid, ledger, prov, cost, router)

    prov.record("session_start", "orchestrator", {
        "scenario_id": scenario["scenario_id"],
        "session_id": sid,
        "scenario_path": args.scenario,
    })

    try:
        # Build orchestration plan
        logger.info("[PHASE] Building plan")
        plan = loop.build_plan()
        ledger.write("orchestration_plan", plan)
        prov.record("plan_created", "orchestrator", plan)

        # Strategy manager validates plan
        sm_review = loop.run_strategy_manager_review(plan, "plan")
        ledger.write("phase_reviews/strategy_manager_plan", sm_review)

        # Debate rounds
        rounds_completed = 0
        for round_num in range(1, MAX_ROUNDS + 1):
            logger.info("[PHASE] Debate round %d", round_num)

            turns = loop.run_debate_round(round_num)
            for ak, turn in turns.items():
                ledger.write(f"turns/{ak}_r{round_num}", turn)
                prov.record(f"turn_r{round_num}", ak, turn)

            critiques = loop.run_critique_round(round_num, turns)
            for ak, critique in critiques.items():
                ledger.write(f"critiques/{ak}_r{round_num}", critique)
                prov.record(f"critique_r{round_num}", ak, critique)

            # On-demand agents
            on_demand = router.evaluate_and_spawn(round_num, turns, critiques, loop)
            for ak, result in on_demand.items():
                ledger.write(f"turns/{ak}_r{round_num}", result)
                prov.record(f"on_demand_r{round_num}", ak, result)

            # Strategy manager reviews round
            all_round = {**turns, **critiques, **on_demand}
            sm_review = loop.run_strategy_manager_review(all_round, f"round_{round_num}")
            ledger.write(f"phase_reviews/strategy_manager_r{round_num}", sm_review)

            # Evaluation
            logger.info("[PHASE] Evaluating round %d", round_num)
            scorecard = loop.run_evaluation(round_num)
            ledger.write(f"evaluation_r{round_num}", scorecard)
            prov.record(f"evaluation_r{round_num}", "evaluation_lead", scorecard)
            rounds_completed = round_num

            if scorecard["quality_verdict"] != "needs_additional_round":
                logger.info("Evaluation passed after round %d", round_num)
                break
            if round_num == MAX_ROUNDS:
                logger.warning("Max rounds reached.")
                break
            logger.info("Additional round requested. Proceeding to round %d.", round_num + 1)

        # Gate review — ethics, compliance, security
        logger.info("[PHASE] Gate review")
        gates = loop.run_gate_review()
        for gate_name, verdict in gates.items():
            ledger.write(f"{gate_name}_verdict", verdict)
            prov.record(f"gate_{gate_name}", gate_name, verdict)

        # Enforce automatic blocks
        blocked = []
        for gate_name, verdict in gates.items():
            if (verdict.get("gate_result") == "block"
                    or verdict.get("prohibited_practice")
                    or verdict.get("injection_detected")):
                blocked.append((gate_name, verdict))

        if blocked:
            logger.warning("BLOCKED by: %s", [b[0] for b in blocked])
            report = render_escalation_report(scenario, sid, blocked, gates, ledger)
            out_path = save_report(scenario["scenario_id"], sid, report, escalation=True)
            prov.record("session_blocked", "orchestrator", {
                "blocked_by": [b[0] for b in blocked],
                "report_path": str(out_path),
            })
            ledger.finalise(cost.summary())
            print(f"\n⛔ Escalation report: {out_path}")
            sys.exit(2)

        # Adjudication
        logger.info("[PHASE] Adjudication")
        final_result = loop.run_adjudication(rounds_completed, gates)
        final_result["cost_usd"] = round(cost.total_usd, 4)
        final_result["rounds_completed"] = rounds_completed
        ledger.write("final_result", final_result)
        prov.record("final_result", "orchestrator", final_result)

        # Report
        logger.info("[PHASE] Writing report")
        report = render_report(scenario, sid, final_result, gates, ledger)
        out_path = save_report(scenario["scenario_id"], sid, report)
        prov.record("report_written", "orchestrator", {"path": str(out_path)})
        ledger.finalise(cost.summary())

        print(f"\n✅ Report: {out_path}")
        print(f"💰 Cost: ${cost.total_usd:.4f}")

        if final_result.get("human_escalation_required"):
            logger.warning("Human escalation required.")
            sys.exit(2)

    except Exception as e:
        logger.exception("Fatal error: %s", e)
        prov.record("fatal_error", "orchestrator", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
