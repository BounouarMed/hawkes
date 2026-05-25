"""
Generate structured prompts for each agent role.
Usage: python src/agent_prompt.py --agent <key> --session <id> --round <n>
                                   --task <debate_turn|critique|evaluation|
                                           strategy_manager|gate|adjudication|on_demand>
                                   [--target <agent>]   # for critique
                                   [--phase <label>]    # for strategy_manager
Prints: full agent prompt to stdout (pass to Agent tool)
"""
import argparse
import json
from pathlib import Path

from src.session_ledger import SessionLedger

PROMPT_DIR = Path("prompts")
DEBATE_POSITIONS = {"product_strategist": "pro", "research_liaison": "con"}
CORE_AGENTS = list(DEBATE_POSITIONS.keys())


def _sys(agent_key: str) -> str:
    for p in [
        PROMPT_DIR / "system" / f"{agent_key}.md",
        PROMPT_DIR / "system" / "on_demand" / f"{agent_key}.md",
    ]:
        if p.exists():
            return p.read_text(encoding="utf-8")
    return f"You are the {agent_key} agent."


def _protocol(name: str) -> str:
    p = PROMPT_DIR / "protocols" / f"{name}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _prior_turns(ledger: SessionLedger, up_to_round: int) -> list:
    turns = []
    for r in range(1, up_to_round):
        for ak in CORE_AGENTS:
            t = ledger.read(f"turns/{ak}_r{r}")
            if t:
                turns.append(t)
    on_demand = ledger.read_pattern("turns__*")
    for t in on_demand:
        if t.get("agent") not in CORE_AGENTS and t not in turns:
            turns.append(t)
    return turns


def _abs(session_id: str, relative: str) -> str:
    return str(Path.cwd() / "sessions" / session_id / relative)


# ─── Prompt builders ────────────────────────────────────────────────────────

def debate_turn(agent_key: str, session_id: str, round_num: int,
                ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    position = DEBATE_POSITIONS.get(agent_key, "neutral")
    opposing_key = [k for k in CORE_AGENTS if k != agent_key][0] \
        if agent_key in CORE_AGENTS else None
    opposing_turns = ledger.read_pattern(f"turns__{opposing_key}_r*") \
        if opposing_key else []
    prior = _prior_turns(ledger, round_num)
    protocol = _protocol("steelman_round" if round_num > 1 else "debate_round")
    phase = "initial_positions" if round_num == 1 else "steelman_rebuttal"
    out = _abs(session_id, f"turns__{agent_key}_r{round_num}.json")

    return f"""{_sys(agent_key)}

---

## Task — Debate Turn

Scenario ID : {scenario.get("scenario_id", "")}
Question    : {scenario.get("question", "").strip()}
Context     : {scenario.get("context", "").strip()}
Your position: {position.upper()}
Round       : {round_num}

## Debate protocol
{protocol}

## Prior turns (rounds before this one)
{json.dumps(prior, indent=2) if prior else "None — this is round 1."}

## Opposing agent prior turns
{json.dumps(opposing_turns, indent=2) if opposing_turns else "None."}

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure (fill in real values — do NOT copy this verbatim):
```json
{{
  "scenario_id": "{scenario.get("scenario_id", "")}",
  "phase": "{phase}",
  "round": {round_num},
  "agent": "{agent_key}",
  "position": "{position}",
  "claims": [
    {{
      "claim_id": "c1",
      "text": "Your claim",
      "evidence_status": "plausible",
      "source_hint": "optional reference"
    }}
  ],
  "steelman_of_opposing": "Minimum 20 words articulating the strongest version of the opposing position",
  "weaknesses": ["Your top weakness 1", "weakness 2", "weakness 3"],
  "uncertainties": ["What you are genuinely uncertain about"],
  "on_demand_requests": [],
  "compliance_concern": false,
  "security_concern": false,
  "confidence": 0.75
}}
```

Constraints:
- steelman_of_opposing: at least 20 words
- weaknesses: 1–4 items, be honest
- claims: 1–6 items, every claim must have an evidence_status
- confidence: 0.0–1.0 based on evidence quality, not rhetorical strength
- Write only the JSON file. No other output.
"""


def critique(critic_key: str, target_key: str, session_id: str,
             round_num: int, ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    target_turn = ledger.read(f"turns/{target_key}_r{round_num}")
    if not target_turn:
        candidates = ledger.read_pattern(f"turns__{target_key}_r*")
        target_turn = candidates[-1] if candidates else {}
    protocol = _protocol("critique_round")
    out = _abs(session_id, f"critiques__{critic_key}_r{round_num}.json")

    return f"""{_sys(critic_key)}

---

## Task — Critique Round

Scenario ID  : {scenario.get("scenario_id", "")}
Your role    : Critic
You critique : {target_key}
Round        : {round_num}

## Critique protocol
{protocol}

## Turn you are critiquing
```json
{json.dumps(target_turn, indent=2)}
```

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure:
```json
{{
  "scenario_id": "{scenario.get("scenario_id", "")}",
  "round": {round_num},
  "critic_agent": "{critic_key}",
  "target_agent": "{target_key}",
  "strongest_point": "The single best point in the opposing argument",
  "top_weaknesses": ["Costly weakness 1", "weakness 2", "weakness 3"],
  "corrections": ["Minimum correction for weakness 1", "correction 2"],
  "verdict": "pass",
  "on_demand_requests": []
}}
```

verdict must be: pass | revise | block
Write only the JSON file. No other output.
"""


def evaluation(session_id: str, round_num: int, ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    all_turns = _prior_turns(ledger, round_num + 1)
    all_critiques = ledger.read_pattern("critiques__*")
    out = _abs(session_id, f"evaluation_r{round_num}.json")

    return f"""{_sys("evaluation_lead")}

---

## Task — Score Round {round_num}

Scenario ID : {scenario.get("scenario_id", "")}
Round       : {round_num}

## All debate turns
```json
{json.dumps(all_turns, indent=2)}
```

## All critiques
```json
{json.dumps(all_critiques, indent=2)}
```

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure:
```json
{{
  "scenario_id": "{scenario.get("scenario_id", "")}",
  "round": {round_num},
  "scores": {{
    "evidence_quality": 0.0,
    "argument_charity": 0.0,
    "claim_coverage": 0.0,
    "uncertainty_honesty": 0.0,
    "steelman_quality": 0.0
  }},
  "contradictions": ["contradiction 1"],
  "unresolved_claims": ["claim still unresolved"],
  "quality_verdict": "pass",
  "additional_round_reason": ""
}}
```

quality_verdict: pass | needs_additional_round | block
Rule: if evidence_quality < 0.6 OR unresolved_claims has > 3 items → needs_additional_round
Write only the JSON file. No other output.
"""


def strategy_manager(session_id: str, phase: str,
                     payload: dict, ledger: SessionLedger) -> str:
    out = _abs(session_id,
               f"phase_reviews__strategy_manager_{phase}.json")
    return f"""{_sys("strategy_manager")}

---

## Task — Phase Review: {phase}

Review the outputs below for coherence, duplication, and protocol gaps.

## Phase payload
```json
{json.dumps(payload, indent=2)}
```

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure:
```json
{{
  "phase": "{phase}",
  "issues": ["any process issues found"],
  "duplications": ["any duplicated claims across agents"],
  "gaps": ["required fields missing or topics unaddressed"],
  "backlog": ["items still unresolved after this phase"]
}}
```

Write only the JSON file. No other output.
"""


def gate(agent_key: str, session_id: str, ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    all_content = json.dumps(ledger.read_all(), indent=2)[:8000]

    schemas = {
        "ethics_lead": {
            "out": _abs(session_id, "ethics_lead_verdict.json"),
            "struct": """{
  "gate_result": "pass",
  "issues_found": [],
  "pii_detected": false,
  "manipulation_risk": "none",
  "prohibited_practice": false,
  "ai_act_article_5_concern": false,
  "compliance_flags": [],
  "recommendation": "string"
}""",
            "notes": "gate_result: pass|pass_with_warnings|block  "
                     "manipulation_risk: none|low|medium|high  "
                     "CRITICAL: prohibited_practice=true → block",
        },
        "compliance_manager": {
            "out": _abs(session_id, "compliance_manager_verdict.json"),
            "struct": """{
  "gate_result": "pass",
  "legal_basis_present": true,
  "gdpr_concern": false,
  "ai_act_concern": false,
  "ai_act_articles": [],
  "transfer_risk": false,
  "flags": [],
  "required_actions": [],
  "recommendation": "string"
}""",
            "notes": "gate_result: pass|pass_with_warnings|block",
        },
        "security_specialist": {
            "out": _abs(session_id, "security_specialist_verdict.json"),
            "struct": """{
  "gate_result": "pass",
  "threats_found": [],
  "injection_detected": false,
  "exfiltration_risk": "none",
  "adversarial_patterns": [],
  "recommendation": "string"
}""",
            "notes": "gate_result: pass|pass_with_warnings|block  "
                     "exfiltration_risk: none|low|medium|high  "
                     "CRITICAL: injection_detected=true → block",
        },
    }

    cfg = schemas[agent_key]
    return f"""{_sys(agent_key)}

---

## Task — Gate Review

Scenario ID: {scenario.get("scenario_id", "")}

## Full session content (truncated)
{all_content}

---

## Output

Use the Write tool to write valid JSON to:
`{cfg["out"]}`

Required structure:
```json
{cfg["struct"]}
```

Notes: {cfg["notes"]}
Be conservative: when in doubt, flag. Write only the JSON file.
"""


def adjudication(session_id: str, rounds_completed: int,
                 ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    all_turns = _prior_turns(ledger, 999)
    gates = {
        "ethics": ledger.read("ethics_lead_verdict") or {},
        "compliance": ledger.read("compliance_manager_verdict") or {},
        "security": ledger.read("security_specialist_verdict") or {},
    }
    evals = ledger.read_pattern("evaluation_r*")
    protocol = _protocol("adjudication")
    out = _abs(session_id, "final_result.json")

    return f"""{_sys("orchestrator")}

---

## Task — Final Adjudication

Scenario ID      : {scenario.get("scenario_id", "")}
Question         : {scenario.get("question", "").strip()}
Rounds completed : {rounds_completed}

## All debate turns
```json
{json.dumps(all_turns, indent=2)}
```

## Gate verdicts
```json
{json.dumps(gates, indent=2)}
```

## Evaluation scorecards
```json
{json.dumps(evals, indent=2)}
```

## Adjudication protocol
{protocol}

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure:
```json
{{
  "scenario_id": "{scenario.get("scenario_id", "")}",
  "verdict": "conditional_recommend",
  "winning_position": "hybrid",
  "rationale": ["reason 1", "reason 2"],
  "blocking_issues": [],
  "conditions": ["condition if any"],
  "human_escalation_required": false,
  "escalation_reason": ""
}}
```

verdict: recommend | conditional_recommend | reject | escalate
winning_position: pro | con | hybrid | none
Write only the JSON file. No other output.
"""


def on_demand(agent_key: str, session_id: str, round_num: int,
              ledger: SessionLedger) -> str:
    scenario = ledger.read("scenario") or {}
    all_turns = _prior_turns(ledger, round_num + 1)
    out = _abs(session_id, f"turns__{agent_key}_r{round_num}.json")

    return f"""{_sys(agent_key)}

---

## Task — On-Demand Domain Contribution

Scenario ID    : {scenario.get("scenario_id", "")}
Question       : {scenario.get("question", "").strip()}
Context        : {scenario.get("context", "").strip()}
Round          : {round_num}
Your position  : NEUTRAL (domain specialist)

## All prior debate turns
```json
{json.dumps(all_turns, indent=2)}
```

---

## Output

Use the Write tool to write valid JSON to:
`{out}`

Required structure:
```json
{{
  "scenario_id": "{scenario.get("scenario_id", "")}",
  "phase": "on_demand",
  "round": {round_num},
  "agent": "{agent_key}",
  "position": "neutral",
  "claims": [
    {{
      "claim_id": "c1",
      "text": "Your domain insight here",
      "evidence_status": "plausible",
      "source_hint": "optional"
    }}
  ],
  "steelman_of_opposing": "In the strongest reading, the position being supplemented argues that...",
  "weaknesses": ["Domain-specific weakness you identified"],
  "uncertainties": ["What remains uncertain from your domain view"],
  "on_demand_requests": [],
  "confidence": 0.75
}}
```

steelman_of_opposing: minimum 20 words
Write only the JSON file. No other output.
"""


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--target")
    parser.add_argument("--phase")
    parser.add_argument(
        "--task", required=True,
        choices=["debate_turn", "critique", "evaluation", "strategy_manager",
                 "gate", "adjudication", "on_demand"],
    )
    args = parser.parse_args()
    ledger = SessionLedger(args.session)

    dispatch = {
        "debate_turn":      lambda: debate_turn(args.agent, args.session, args.round, ledger),
        "critique":         lambda: critique(args.agent, args.target, args.session, args.round, ledger),
        "evaluation":       lambda: evaluation(args.session, args.round, ledger),
        "strategy_manager": lambda: strategy_manager(
            args.session, args.phase or "unknown", ledger.read_all(), ledger),
        "gate":             lambda: gate(args.agent, args.session, ledger),
        "adjudication":     lambda: adjudication(args.session, args.round, ledger),
        "on_demand":        lambda: on_demand(args.agent, args.session, args.round, ledger),
    }
    print(dispatch[args.task]())


if __name__ == "__main__":
    main()
