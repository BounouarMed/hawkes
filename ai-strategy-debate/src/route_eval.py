"""
Evaluate routing rules and return on-demand agents to spawn.
Usage: python src/route_eval.py --session <id> --round <n>
Prints: JSON {"agents_to_spawn": [...]}
"""
import argparse
import json

from src.session_ledger import SessionLedger
from src.router import Router


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True)
    parser.add_argument("--round", type=int, default=1)
    args = parser.parse_args()

    ledger = SessionLedger(args.session)
    scenario = ledger.read("scenario") or {}

    all_data = ledger.read_all()
    turns, critiques = {}, {}
    for key, data in all_data.items():
        if f"turns/" in key and f"_r{args.round}" in key:
            agent = key.split("/")[-1].replace(f"_r{args.round}", "")
            turns[agent] = data
        if f"critiques/" in key and f"_r{args.round}" in key:
            agent = key.split("/")[-1].replace(f"_r{args.round}", "")
            critiques[agent] = data

    router = Router(scenario, ledger)
    triggered = router._evaluate_rules(args.round, turns, critiques)

    on_demand_keys = {
        "mlops_strategist", "business_analyst", "ux_researcher",
        "knowledge_engineer", "cognitive_scientist", "computational_linguist",
        "prompt_engineer", "change_manager",
    }
    already_spawned = {
        key.split("/")[-1].rsplit("_r", 1)[0]
        for key in all_data
        if "turns/" in key
        and key.split("/")[-1].rsplit("_r", 1)[0] in on_demand_keys
    }

    to_spawn = sorted(triggered - already_spawned)
    print(json.dumps({"agents_to_spawn": to_spawn}))


if __name__ == "__main__":
    main()
