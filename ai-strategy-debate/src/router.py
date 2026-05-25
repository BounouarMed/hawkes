import logging
import yaml
from pathlib import Path

logger = logging.getLogger("router")

class Router:
    def __init__(self, scenario: dict, ledger):
        self.scenario = scenario
        self.ledger = ledger
        self.rules = self._load_rules()
        self.spawned: set[str] = set()

    def _load_rules(self) -> list[dict]:
        path = Path("agents/routing.yaml")
        if not path.exists():
            return []
        return yaml.safe_load(path.read_text()).get("rules", [])

    def evaluate_and_spawn(self, round_num: int, turns: dict,
                           critiques: dict, loop) -> dict[str, dict]:
        results = {}
        requested = set()
        for turn in turns.values():
            for req in turn.get("on_demand_requests", []):
                if isinstance(req, dict):
                    requested.add(req.get("agent_key", ""))
        for critique in critiques.values():
            for req in critique.get("on_demand_requests", []):
                if isinstance(req, dict):
                    requested.add(req.get("agent_key", ""))

        triggered = self._evaluate_rules(round_num, turns, critiques)
        all_to_spawn = (requested | triggered) - self.spawned - {""}

        for agent_key in all_to_spawn:
            logger.info("Spawning on-demand: %s (round %d)", agent_key, round_num)
            try:
                result = loop.run_on_demand_agent(agent_key, round_num)
                results[agent_key] = result
                self.spawned.add(agent_key)
            except Exception as e:
                logger.error("On-demand agent %s failed: %s", agent_key, e)
        return results

    def _evaluate_rules(self, round_num: int, turns: dict, critiques: dict) -> set[str]:
        triggered = set()
        risk_level = self.scenario.get("constraints", {}).get("risk_level", "low")
        question = self.scenario.get("question", "").lower()

        for turn in turns.values():
            if turn.get("security_concern"):
                triggered.add("mlops_strategist")
            for claim in turn.get("claims", []):
                if claim.get("evidence_status") == "unverified" and not claim.get("source_hint"):
                    triggered.add("knowledge_engineer")

        for critique in critiques.values():
            if isinstance(critique, dict) and critique.get("verdict") == "revise":
                body = str(critique).lower()
                if "kpi" in body or "roi" in body:
                    triggered.add("business_analyst")

        if any(w in question for w in ["user", "customer", "employee", "public"]):
            triggered.add("ux_researcher")
        if risk_level in ["high", "critical"]:
            triggered.add("cognitive_scientist")

        return triggered
