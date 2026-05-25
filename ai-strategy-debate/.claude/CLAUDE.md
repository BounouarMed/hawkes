# AI Strategy Debate System — CLAUDE.md

## What this is

A 9-agent AI strategy debate system running natively inside Claude Code.
Each agent is a Claude subagent with a dedicated system prompt, tool permissions,
and memory scope. The orchestrator spawns subagents, routes work, collects structured
outputs, and produces a traceable human-readable report.

## Quick start

```bash
# Always run safety tests first
/redteam

# Run a debate
/debate --scenario data/scenarios/vendor_selection.yaml
/debate --scenario data/scenarios/risky_use.yaml
/debate --scenario data/scenarios/policy_review.yaml
/debate --scenario data/scenarios/inter_bu_arbitration.yaml

# View results
/report
/score
```

## Architecture

- **Orchestrator** (claude-opus-4-7): plans, routes, arbitrates, writes final report
- **Core agents** (claude-sonnet-4-6): product_strategist [PRO], research_liaison [CON],
  debate_architect, evaluation_lead, strategy_manager, ethics_lead, compliance_manager
- **Security** (claude-haiku-4-5-20251001): security_specialist
- **On-demand** (routing-triggered): mlops_strategist, business_analyst, ux_researcher,
  knowledge_engineer, cognitive_scientist, computational_linguist, prompt_engineer, change_manager

## Debate flow

```
Rounds 1–4: PRO + CON positions → cross-critiques → on-demand agents → evaluation
Gates: ethics + compliance + security (parallel) → block = escalation report
Adjudication → final_result → human report
```

## Outputs

```
reports/<id>_<ts>.md      human report
sessions/<id>/            all structured agent JSON
audits/<id>.jsonl         append-only provenance log
```

## Exit codes

- `0` — success, no escalation required
- `2` — human review required (gate blocked or escalation flagged)
- `1` — fatal error

## Key files

- `src/orchestrator.py` — main entry point
- `src/debate_loop.py` — all agent API calls
- `src/router.py` — on-demand agent routing logic
- `agents/registry.yaml` — agent model/authority config
- `agents/routing.yaml` — routing rules
- `schemas/` — JSON schemas for all structured outputs
- `prompts/system/` — system prompts for all 17 agents
- `prompts/protocols/` — debate, critique, steelman, adjudication, escalation protocols

## Environment variables

```
ANTHROPIC_API_KEY    required
LOG_LEVEL            INFO (default)
MAX_DEBATE_ROUNDS    3 (default, max 4)
COST_ALERT_USD       5.00 (default)
```

## Safety invariants

- `prohibited_practice=true` → automatic block, no exceptions
- `injection_detected=true` → automatic block, no exceptions
- Any gate `block` verdict → escalation report, exit code 2, no recommendation released
- All outputs require human review before decisions are made
