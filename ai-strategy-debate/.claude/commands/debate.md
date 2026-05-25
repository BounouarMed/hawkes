# /debate — AI Strategy Debate Orchestrator

Orchestrate a full multi-agent AI strategy debate using Claude Code subagents.
No external API calls. No API key required. All agent reasoning runs as subagents.

## Usage
/debate --scenario <path>

Example: /debate --scenario data/scenarios/vendor_selection.yaml

---

## ORCHESTRATION INSTRUCTIONS

You are the orchestrator. Follow every step below in order.
Use the Bash tool for Python utilities. Use the Agent tool for all agent reasoning.
All paths are relative to `/home/user/hawkes/ai-strategy-debate/`.

---

## STEP 1 — Initialize session

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/session_init.py --scenario <scenario_path>
```

Capture the printed SESSION_ID. Announce to the user:
> "Starting debate | Scenario: [title] | Session: [SESSION_ID]"

Read scenario to know the title and question:
```bash
cd /home/user/hawkes/ai-strategy-debate && python -c "
import json; s=json.load(open('sessions/<SESSION_ID>/scenario.json'))
print('Title:', s['title'])
print('Question:', s['question'][:120])
print('Risk:', s['constraints']['risk_level'])
"
```

---

## STEP 2 — Debate rounds (repeat up to MAX_ROUNDS=3, or stop when evaluation passes)

Set CURRENT_ROUND = 1. Repeat the following until evaluation passes or CURRENT_ROUND > 3.

### 2a — Initial positions (run both agents IN PARALLEL)

Generate prompt for product_strategist:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent product_strategist --session <SESSION_ID> --round <CURRENT_ROUND> --task debate_turn
```

Generate prompt for research_liaison:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent research_liaison --session <SESSION_ID> --round <CURRENT_ROUND> --task debate_turn
```

Spawn TWO agents in parallel (send both in one message):
- Agent 1: description="product_strategist PRO R<N>", prompt=<product_strategist prompt>
- Agent 2: description="research_liaison CON R<N>", prompt=<research_liaison prompt>

Each agent will use the Write tool to write its JSON output file.
Wait for both to complete before continuing.

Validate:
```bash
cd /home/user/hawkes/ai-strategy-debate && python -c "
import json
from src.schema_validator import is_valid
sid = '<SESSION_ID>'; r = <CURRENT_ROUND>
for ag in ['product_strategist', 'research_liaison']:
    try:
        d = json.load(open(f'sessions/{sid}/turns__{ag}_r{r}.json'))
        print(f'{ag}: valid={is_valid(d, \"debate_turn\")}')
    except FileNotFoundError:
        print(f'{ag}: FILE MISSING — agent may not have written output')
"
```

If a file is missing: re-spawn that agent with the same prompt.

### 2b — Cross-critiques (run sequentially)

Generate and spawn product_strategist critiquing research_liaison:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent product_strategist --session <SESSION_ID> --round <CURRENT_ROUND> \
  --target research_liaison --task critique
```
Spawn Agent: description="product_strategist critique R<N>", prompt=<above>

Then generate and spawn research_liaison critiquing product_strategist:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent research_liaison --session <SESSION_ID> --round <CURRENT_ROUND> \
  --target product_strategist --task critique
```
Spawn Agent: description="research_liaison critique R<N>", prompt=<above>

### 2c — On-demand routing

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/route_eval.py \
  --session <SESSION_ID> --round <CURRENT_ROUND>
```

For each agent in `agents_to_spawn` (run in parallel if multiple):
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent <agent_key> --session <SESSION_ID> --round <CURRENT_ROUND> --task on_demand
```
Spawn Agent: description="<agent_key> on-demand R<N>", prompt=<above>

Announce which on-demand agents were triggered (or "No on-demand agents triggered").

### 2d — Strategy manager review

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent strategy_manager --session <SESSION_ID> --round <CURRENT_ROUND> \
  --task strategy_manager --phase round_<CURRENT_ROUND>
```
Spawn Agent: description="strategy_manager review R<N>", prompt=<above>

### 2e — Evaluation

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent evaluation_lead --session <SESSION_ID> --round <CURRENT_ROUND> --task evaluation
```
Spawn Agent: description="evaluation_lead R<N>", prompt=<above>

Read verdict:
```bash
cd /home/user/hawkes/ai-strategy-debate && python -c "
import json
e = json.load(open('sessions/<SESSION_ID>/evaluation_r<CURRENT_ROUND>.json'))
print('verdict:', e['quality_verdict'])
print('avg score:', sum(e['scores'].values())/len(e['scores']) if e.get('scores') else 'n/a')
print('unresolved:', len(e.get('unresolved_claims',[])))
"
```

**Decision**:
- If `quality_verdict == pass` → stop rounds, go to STEP 3
- If `quality_verdict == needs_additional_round` AND CURRENT_ROUND < 3 → increment CURRENT_ROUND, repeat from 2a
- If CURRENT_ROUND == 3 → stop regardless, go to STEP 3

Announce round result to user.

---

## STEP 3 — Gate review (run all 3 IN PARALLEL)

Generate prompts:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent ethics_lead --session <SESSION_ID> --task gate

python src/agent_prompt.py \
  --agent compliance_manager --session <SESSION_ID> --task gate

python src/agent_prompt.py \
  --agent security_specialist --session <SESSION_ID> --task gate
```

Spawn THREE agents in parallel (send all in one message):
- Agent 1: description="ethics_lead gate", prompt=<ethics prompt>
- Agent 2: description="compliance_manager gate", prompt=<compliance prompt>
- Agent 3: description="security_specialist gate", prompt=<security prompt>

Wait for all three. Then check:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/gate_check.py --session <SESSION_ID>
```

**If `status == "blocked"`**:
```bash
cd /home/user/hawkes/ai-strategy-debate && python src/render_report.py \
  --session <SESSION_ID> --escalation
```
Alert user: "⛔ BLOCKED — [which gates] — Escalation report: [path]"
**STOP. Do not proceed to adjudication.**

If clear, show user which gates passed (and any warnings).

---

## STEP 4 — Adjudication

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/agent_prompt.py \
  --agent orchestrator --session <SESSION_ID> --round <ROUNDS_COMPLETED> --task adjudication
```
Spawn Agent: description="orchestrator adjudication", prompt=<above>

Record session cost (no API cost — all ran as subagents):
```bash
cd /home/user/hawkes/ai-strategy-debate && python -c "
from src.session_ledger import SessionLedger
SessionLedger('<SESSION_ID>').finalise({
  'total_usd': 0,
  'note': 'Ran as Claude Code subagents — no direct API cost',
  'rounds_completed': <ROUNDS_COMPLETED>,
})
"
```

---

## STEP 5 — Render and display report

```bash
cd /home/user/hawkes/ai-strategy-debate && python src/render_report.py --session <SESSION_ID>
```

Read and display the full report content to the user using the Read tool.

Announce:
> "✅ Debate complete | Session: [SESSION_ID] | Report: [path] | Rounds: [N]"

If `final_result.human_escalation_required == true`:
> "⚠️ Human escalation required: [escalation_reason]"

---

## ERROR HANDLING

- If an agent does not write its output file: re-spawn once with the same prompt
- If schema validation fails: note the issue in your summary but continue
- If a round produces no turns at all: skip evaluation and go to gates
- Always write the provenance log entry after each major phase using:
  ```bash
  cd /home/user/hawkes/ai-strategy-debate && python -c "
  from src.provenance import ProvenanceLog
  ProvenanceLog('<SESSION_ID>').record('<event>', 'orchestrator', {<payload>})
  "
  ```

---

## PARALLEL EXECUTION RULE

When the instructions say "run in parallel" — send a SINGLE message with
MULTIPLE Agent tool calls. This is the only way subagents actually run
concurrently. Never send parallel agents in separate messages.
