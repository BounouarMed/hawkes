from datetime import datetime, timezone
from src.session_ledger import SessionLedger

def render_report(scenario, session_id, final_result, gates, ledger: SessionLedger) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    all_turns = ledger.read_pattern("turns__*")
    evals = ledger.read_pattern("evaluation_r*")

    gate_lines = []
    for gate, v in gates.items():
        icon = "✅" if v["gate_result"] == "pass" else ("⚠️" if v["gate_result"] == "pass_with_warnings" else "🚫")
        gate_lines.append(f"{icon} **{gate}**: {v['gate_result']}")

    pro_claims, con_claims = [], []
    for t in all_turns:
        target = pro_claims if t.get("position") == "pro" else con_claims if t.get("position") == "con" else None
        if target is not None:
            for c in t.get("claims", []):
                target.append(f"- [{c['evidence_status']}] {c['text']}")

    eval_lines = []
    for ev in evals:
        scores = ev.get("scores", {})
        avg = sum(scores.values()) / len(scores) if scores else 0
        eval_lines.append(f"- Round {ev.get('round','?')}: avg {avg:.2f} | {ev.get('quality_verdict','?')}")

    icons = {"recommend":"✅","conditional_recommend":"⚠️","reject":"🚫","escalate":"🔴"}
    verdict_icon = icons.get(final_result["verdict"], "?")

    return f"""# AI Strategy Debate Report

> ⚠️ **AI-Generated Output**: Produced by a multi-agent AI debate system.
> Requires human review before any decision. Do not act without validation.

**Scenario**: {scenario['title']}
**Session**: `{session_id}`
**Generated**: {ts}
**Cost**: ${final_result.get('cost_usd', 0):.4f} | **Rounds**: {final_result.get('rounds_completed', '?')}

---

## Executive Summary

**Verdict**: {verdict_icon} `{final_result['verdict'].upper()}`
**Winning position**: `{final_result['winning_position']}`

{chr(10).join(f'- {r}' for r in final_result.get('rationale', []))}

---

## Question

> {scenario['question']}

---

## PRO position

{chr(10).join(pro_claims) or '_No PRO claims recorded._'}

---

## CON position

{chr(10).join(con_claims) or '_No CON claims recorded._'}

---

## Debate quality

{chr(10).join(eval_lines) or '_No evaluation data._'}

---

## Gate results

{chr(10).join(gate_lines)}

---

## Blocking issues

{chr(10).join(f'- {i}' for i in final_result.get('blocking_issues', [])) or '_None._'}

## Conditions

{chr(10).join(f'- {c}' for c in final_result.get('conditions', [])) or '_None._'}

---

## Human escalation

**Required**: {'Yes' if final_result.get('human_escalation_required') else 'No'}
{f"**Reason**: {final_result.get('escalation_reason','')}" if final_result.get('human_escalation_required') else ''}

---

## Provenance

- `sessions/{session_id}/` — all structured agent outputs
- `audits/{session_id}.jsonl` — append-only event log
"""

def render_escalation_report(scenario, session_id, blocked, gates, ledger: SessionLedger) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections = []
    for gate_name, verdict in blocked:
        issues = verdict.get("issues_found", verdict.get("threats_found", verdict.get("flags", [])))
        issue_lines = "\n".join(f"  - {i}" for i in issues)
        sections.append(
            f"### {gate_name}\n\n**Result**: {verdict['gate_result']}\n\n"
            f"**Issues**:\n{issue_lines}\n\n"
            f"**Recommendation**: {verdict.get('recommendation','')}"
        )
    return f"""# ⛔ ESCALATION REPORT — Output Blocked

> No recommendation released. Human review mandatory.

**Scenario**: {scenario['title']}
**Session**: `{session_id}`
**Generated**: {ts}

---

## Blocked gates

{chr(10).join(sections)}

---

## What the reviewer must decide

1. Review full debate in `sessions/{session_id}/`
2. Assess whether blocking issues can be resolved
3. If proceeding: document legal basis, involve DPO if required, then rerun
4. If not: document decision and archive session

**Audit trail**: `audits/{session_id}.jsonl`
"""
