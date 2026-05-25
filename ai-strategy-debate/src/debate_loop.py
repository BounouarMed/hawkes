"""
Debate loop — manages round execution and all agent invocations.
Each agent = one client.messages.create() call with a strict tool schema.
"""
import json
import logging
from pathlib import Path
import anthropic

from src.schema_validator import validate, ValidationError
from src.cost_tracker import CostTracker, PRICING
from src.session_ledger import SessionLedger

logger = logging.getLogger("debate_loop")

MODELS = {
    "orchestrator":           "claude-opus-4-7",
    "strategy_manager":       "claude-sonnet-4-6",
    "product_strategist":     "claude-sonnet-4-6",
    "research_liaison":       "claude-sonnet-4-6",
    "debate_architect":       "claude-sonnet-4-6",
    "evaluation_lead":        "claude-sonnet-4-6",
    "ethics_lead":            "claude-sonnet-4-6",
    "compliance_manager":     "claude-sonnet-4-6",
    "security_specialist":    "claude-haiku-4-5-20251001",
    "mlops_strategist":       "claude-sonnet-4-6",
    "business_analyst":       "claude-sonnet-4-6",
    "ux_researcher":          "claude-sonnet-4-6",
    "knowledge_engineer":     "claude-sonnet-4-6",
    "cognitive_scientist":    "claude-sonnet-4-6",
    "computational_linguist": "claude-haiku-4-5-20251001",
    "prompt_engineer":        "claude-haiku-4-5-20251001",
    "change_manager":         "claude-sonnet-4-6",
}

DEBATE_POSITIONS = {
    "product_strategist": "pro",
    "research_liaison":   "con",
}
CORE_AGENTS = list(DEBATE_POSITIONS.keys())
CRITIQUE_PAIRS = [("product_strategist","research_liaison"),
                  ("research_liaison","product_strategist")]

GATE_AGENTS = {
    "ethics_lead":     ("emit_ethics_verdict",     "ethics_verdict"),
    "compliance_manager": ("emit_compliance_verdict", "compliance_verdict"),
    "security_specialist": ("emit_security_verdict",  "security_verdict"),
}


class DebateLoop:
    def __init__(self, scenario, session_id, ledger: SessionLedger,
                 prov, cost: CostTracker, router):
        self.scenario = scenario
        self.session_id = session_id
        self.ledger = ledger
        self.prov = prov
        self.cost = cost
        self.router = router
        self.client = anthropic.Anthropic()
        self.prompt_dir = Path("prompts")

    def _load_prompt(self, agent_key: str) -> str:
        for p in [
            self.prompt_dir / "system" / f"{agent_key}.md",
            self.prompt_dir / "system" / "on_demand" / f"{agent_key}.md",
        ]:
            if p.exists():
                return p.read_text(encoding="utf-8")
        raise FileNotFoundError(f"No prompt for agent: {agent_key}")

    def _call(self, agent_key: str, user_content: str,
              tool_name: str, tool_schema: dict, schema_name: str,
              max_tokens: int = 2048) -> dict:
        model = MODELS[agent_key]
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=self._load_prompt(agent_key),
            tools=[{"name": tool_name,
                    "description": f"Emit structured output for {agent_key}. No prose outside the schema.",
                    "input_schema": tool_schema}],
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": user_content}],
        )
        inp, out = response.usage.input_tokens, response.usage.output_tokens
        cost_usd = self.cost.compute(model, inp, out)
        self.cost.record(agent_key, model, cost_usd, inp, out)

        for block in response.content:
            if block.type == "tool_use":
                output = block.input
                try:
                    validate(output, schema_name)
                except ValidationError as e:
                    logger.warning("Schema warning for %s: %s", agent_key, e)
                return output
        raise RuntimeError(f"{agent_key} did not emit tool call. stop_reason={response.stop_reason}")

    def _turn_schema(self) -> dict:
        return {
            "type":"object",
            "required":["scenario_id","phase","round","agent","position","claims",
                        "steelman_of_opposing","weaknesses","uncertainties",
                        "on_demand_requests","confidence"],
            "properties":{
                "scenario_id":{"type":"string"}, "phase":{"type":"string"},
                "round":{"type":"integer"}, "agent":{"type":"string"},
                "position":{"type":"string","enum":["pro","con","neutral"]},
                "claims":{"type":"array","minItems":1,"items":{
                    "type":"object","required":["claim_id","text","evidence_status"],
                    "properties":{
                        "claim_id":{"type":"string"},"text":{"type":"string"},
                        "evidence_status":{"type":"string","enum":["supported","plausible","speculative","unverified","contested"]},
                        "source_hint":{"type":"string"},"rebutted_by":{"type":"string"}
                    }}},
                "steelman_of_opposing":{"type":"string","minLength":20},
                "weaknesses":{"type":"array","minItems":1,"items":{"type":"string"}},
                "uncertainties":{"type":"array","items":{"type":"string"}},
                "on_demand_requests":{"type":"array","items":{"type":"object",
                    "required":["agent_key","reason"],
                    "properties":{"agent_key":{"type":"string"},"reason":{"type":"string"}}}},
                "compliance_concern":{"type":"boolean"},"security_concern":{"type":"boolean"},
                "confidence":{"type":"number","minimum":0,"maximum":1}
            }
        }

    def build_plan(self) -> dict:
        schema = {
            "type":"object",
            "required":["scenario_id","active_agents","phases","debate_positions","routing_rules","max_rounds"],
            "properties":{
                "scenario_id":{"type":"string"},
                "active_agents":{"type":"array","items":{"type":"string"}},
                "on_demand_triggers":{"type":"array","items":{"type":"string"}},
                "phases":{"type":"array","items":{"type":"object","required":["phase_id","phase_type","agents","parallel"],
                    "properties":{"phase_id":{"type":"string"},"phase_type":{"type":"string"},
                        "agents":{"type":"array","items":{"type":"string"}},"parallel":{"type":"boolean"},
                        "depends_on":{"type":"array","items":{"type":"string"}}}}},
                "debate_positions":{"type":"object","properties":{
                    "pro":{"type":"array","items":{"type":"string"}},
                    "con":{"type":"array","items":{"type":"string"}}}},
                "routing_rules":{"type":"array","items":{"type":"string"}},
                "max_rounds":{"type":"integer","minimum":1,"maximum":4}
            }
        }
        content = (
            f"<scenario>\n{json.dumps(self.scenario, indent=2)}\n</scenario>\n\n"
            "Build an orchestration plan for this scenario. Include all 9 core agents. "
            "Identify on-demand agent triggers. Set max_rounds to 3. "
            "Emit using the emit_orchestration_plan tool."
        )
        return self._call("orchestrator", content, "emit_orchestration_plan", schema, "orchestration_plan")

    def run_debate_round(self, round_num: int) -> dict[str, dict]:
        protocol_file = "steelman_round.md" if round_num > 1 else "debate_round.md"
        protocol = (self.prompt_dir / "protocols" / protocol_file).read_text()
        prior = self._all_prior_turns(round_num)
        results = {}

        for agent_key in CORE_AGENTS:
            position = DEBATE_POSITIONS[agent_key]
            opposing_key = [k for k in CORE_AGENTS if k != agent_key][0]
            opposing_turns = self.ledger.read_pattern(f"turns__{opposing_key}_r*")

            content = (
                f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
                f"<question>{self.scenario['question']}</question>\n"
                f"<context>{self.scenario.get('context','')}</context>\n"
                f"<your_position>{position.upper()}</your_position>\n"
                f"<round>{round_num}</round>\n"
                f"<protocol>\n{protocol}\n</protocol>\n"
            )
            if prior:
                content += f"<all_prior_turns>\n{json.dumps(prior, indent=2)}\n</all_prior_turns>\n"
            if opposing_turns:
                content += f"<opposing_turns>\n{json.dumps(opposing_turns, indent=2)}\n</opposing_turns>\n"
            content += "\nEmit your debate turn using the emit_debate_turn tool."

            result = self._call(agent_key, content, "emit_debate_turn", self._turn_schema(), "debate_turn")
            results[agent_key] = result
        return results

    def run_critique_round(self, round_num: int, turns: dict[str, dict]) -> dict[str, dict]:
        protocol = (self.prompt_dir / "protocols" / "critique_round.md").read_text()
        critique_schema = {
            "type":"object",
            "required":["scenario_id","round","critic_agent","target_agent",
                        "strongest_point","top_weaknesses","corrections","verdict"],
            "properties":{
                "scenario_id":{"type":"string"},"round":{"type":"integer"},
                "critic_agent":{"type":"string"},"target_agent":{"type":"string"},
                "strongest_point":{"type":"string"},
                "top_weaknesses":{"type":"array","items":{"type":"string"}},
                "corrections":{"type":"array","items":{"type":"string"}},
                "verdict":{"type":"string","enum":["pass","revise","block"]},
                "on_demand_requests":{"type":"array","items":{"type":"object"}}
            }
        }
        results = {}
        for critic_key, target_key in CRITIQUE_PAIRS:
            target_turn = turns.get(target_key) or self.ledger.read_pattern(f"turns__{target_key}_r*")
            if isinstance(target_turn, list):
                target_turn = target_turn[-1] if target_turn else None
            if not target_turn:
                continue
            content = (
                f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
                f"<round>{round_num}</round>\n"
                f"<critic>{critic_key}</critic>\n"
                f"<target_agent>{target_key}</target_agent>\n"
                f"<target_turn>\n{json.dumps(target_turn, indent=2)}\n</target_turn>\n"
                f"<protocol>\n{protocol}\n</protocol>\n\n"
                "Emit your critique using the emit_critique_report tool."
            )
            results[critic_key] = self._call(critic_key, content, "emit_critique_report",
                                              critique_schema, "critique_report")
        return results

    def run_on_demand_agent(self, agent_key: str, round_num: int) -> dict:
        all_turns = self._all_prior_turns(round_num + 1)
        content = (
            f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
            f"<question>{self.scenario['question']}</question>\n"
            f"<context>{self.scenario.get('context','')}</context>\n"
            f"<round>{round_num}</round>\n"
            f"<all_prior_turns>\n{json.dumps(all_turns, indent=2)}\n</all_prior_turns>\n\n"
            "You have been called as a domain specialist. Provide your neutral contribution. "
            "Emit using the emit_debate_turn tool."
        )
        return self._call(agent_key, content, "emit_debate_turn", self._turn_schema(), "debate_turn")

    def run_strategy_manager_review(self, payload: dict, phase: str) -> dict:
        schema = {
            "type":"object",
            "required":["phase","issues","duplications","gaps","backlog"],
            "properties":{
                "phase":{"type":"string"},
                "issues":{"type":"array","items":{"type":"string"}},
                "duplications":{"type":"array","items":{"type":"string"}},
                "gaps":{"type":"array","items":{"type":"string"}},
                "backlog":{"type":"array","items":{"type":"string"}},
            }
        }
        content = (
            f"<phase>{phase}</phase>\n"
            f"<payload>\n{json.dumps(payload, indent=2)}\n</payload>\n\n"
            "Review for coherence, duplication, and gaps. Emit using emit_phase_review tool."
        )
        return self._call("strategy_manager", content, "emit_phase_review", schema,
                          "orchestration_plan", max_tokens=1024)

    def run_evaluation(self, round_num: int) -> dict:
        schema = {
            "type":"object",
            "required":["scenario_id","round","scores","contradictions","quality_verdict"],
            "properties":{
                "scenario_id":{"type":"string"},"round":{"type":"integer"},
                "scores":{"type":"object","properties":{
                    "evidence_quality":{"type":"number"},"argument_charity":{"type":"number"},
                    "claim_coverage":{"type":"number"},"uncertainty_honesty":{"type":"number"},
                    "steelman_quality":{"type":"number"}}},
                "contradictions":{"type":"array","items":{"type":"string"}},
                "unresolved_claims":{"type":"array","items":{"type":"string"}},
                "quality_verdict":{"type":"string","enum":["pass","needs_additional_round","block"]},
                "additional_round_reason":{"type":"string"}
            }
        }
        all_turns = self._all_prior_turns(round_num + 1)
        all_critiques = self.ledger.read_pattern("critiques__*")
        content = (
            f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
            f"<round>{round_num}</round>\n"
            f"<all_turns>\n{json.dumps(all_turns, indent=2)}\n</all_turns>\n"
            f"<all_critiques>\n{json.dumps(all_critiques, indent=2)}\n</all_critiques>\n\n"
            "Score this debate round. Emit scorecard using emit_evaluation_scorecard tool."
        )
        return self._call("evaluation_lead", content, "emit_evaluation_scorecard",
                          schema, "evaluation_scorecard")

    def run_gate_review(self) -> dict[str, dict]:
        all_content = json.dumps(self.ledger.read_all(), indent=2)
        gate_schemas = {
            "ethics_lead": {
                "tool": "emit_ethics_verdict", "schema": "ethics_verdict",
                "input_schema": {
                    "type":"object",
                    "required":["gate_result","issues_found","pii_detected","manipulation_risk","prohibited_practice"],
                    "properties":{
                        "gate_result":{"type":"string","enum":["pass","pass_with_warnings","block"]},
                        "issues_found":{"type":"array","items":{"type":"string"}},
                        "pii_detected":{"type":"boolean"},
                        "manipulation_risk":{"type":"string","enum":["none","low","medium","high"]},
                        "prohibited_practice":{"type":"boolean"},
                        "ai_act_article_5_concern":{"type":"boolean"},
                        "compliance_flags":{"type":"array","items":{"type":"string"}},
                        "recommendation":{"type":"string"}
                    }
                },
                "instruction": "Screen debate outputs for ethical risks.",
            },
            "compliance_manager": {
                "tool": "emit_compliance_verdict", "schema": "compliance_verdict",
                "input_schema": {
                    "type":"object",
                    "required":["gate_result","legal_basis_present","gdpr_concern","ai_act_concern","flags"],
                    "properties":{
                        "gate_result":{"type":"string","enum":["pass","pass_with_warnings","block"]},
                        "legal_basis_present":{"type":"boolean"},
                        "gdpr_concern":{"type":"boolean"},
                        "ai_act_concern":{"type":"boolean"},
                        "ai_act_articles":{"type":"array","items":{"type":"string"}},
                        "transfer_risk":{"type":"boolean"},
                        "flags":{"type":"array","items":{"type":"string"}},
                        "required_actions":{"type":"array","items":{"type":"string"}},
                        "recommendation":{"type":"string"}
                    }
                },
                "instruction": "Screen for GDPR, AI Act, and legal basis compliance.",
            },
            "security_specialist": {
                "tool": "emit_security_verdict", "schema": "security_verdict",
                "input_schema": {
                    "type":"object",
                    "required":["gate_result","threats_found","injection_detected","exfiltration_risk"],
                    "properties":{
                        "gate_result":{"type":"string","enum":["pass","pass_with_warnings","block"]},
                        "threats_found":{"type":"array","items":{"type":"string"}},
                        "injection_detected":{"type":"boolean"},
                        "exfiltration_risk":{"type":"string","enum":["none","low","medium","high"]},
                        "adversarial_patterns":{"type":"array","items":{"type":"string"}},
                        "recommendation":{"type":"string"}
                    }
                },
                "instruction": "Red-team outputs for injection, exfiltration, adversarial patterns.",
            },
        }
        results = {}
        truncated = all_content[:8000]
        for agent_key, cfg in gate_schemas.items():
            content = (
                f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
                f"<session_content>\n{truncated}\n</session_content>\n\n"
                f"{cfg['instruction']} Emit verdict using {cfg['tool']} tool."
            )
            results[agent_key] = self._call(agent_key, content, cfg["tool"],
                                             cfg["input_schema"], cfg["schema"], max_tokens=1024)
        return results

    def run_adjudication(self, rounds_completed: int, gates: dict) -> dict:
        schema = {
            "type":"object",
            "required":["scenario_id","verdict","winning_position","rationale",
                        "blocking_issues","conditions","human_escalation_required"],
            "properties":{
                "scenario_id":{"type":"string"},
                "verdict":{"type":"string","enum":["recommend","conditional_recommend","reject","escalate"]},
                "winning_position":{"type":"string","enum":["pro","con","hybrid","none"]},
                "rationale":{"type":"array","items":{"type":"string"}},
                "blocking_issues":{"type":"array","items":{"type":"string"}},
                "conditions":{"type":"array","items":{"type":"string"}},
                "human_escalation_required":{"type":"boolean"},
                "escalation_reason":{"type":"string"}
            }
        }
        protocol = (self.prompt_dir / "protocols" / "adjudication.md").read_text()
        all_turns = self._all_prior_turns(999)
        all_evals = self.ledger.read_pattern("evaluation_r*")
        content = (
            f"<scenario_id>{self.scenario['scenario_id']}</scenario_id>\n"
            f"<question>{self.scenario['question']}</question>\n"
            f"<rounds_completed>{rounds_completed}</rounds_completed>\n"
            f"<all_turns>\n{json.dumps(all_turns, indent=2)}\n</all_turns>\n"
            f"<gate_verdicts>\n{json.dumps(gates, indent=2)}\n</gate_verdicts>\n"
            f"<evaluations>\n{json.dumps(all_evals, indent=2)}\n</evaluations>\n"
            f"<protocol>\n{protocol}\n</protocol>\n\n"
            "Arbitrate and emit final result using emit_final_result tool."
        )
        return self._call("orchestrator", content, "emit_final_result", schema, "final_result")

    def _all_prior_turns(self, up_to_round: int) -> list[dict]:
        turns = []
        for r in range(1, up_to_round):
            for ak in CORE_AGENTS:
                t = self.ledger.read(f"turns/{ak}_r{r}")
                if t:
                    turns.append(t)
        on_demand = self.ledger.read_pattern("turns__*")
        for t in on_demand:
            if t.get("agent") not in CORE_AGENTS and t not in turns:
                turns.append(t)
        return turns
