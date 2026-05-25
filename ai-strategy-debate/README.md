# AI Strategy Debate System

9-agent AI strategy debate system running inside Claude Code.
Produces contradictory, evaluated, ethics-screened, compliance-checked recommendations.

## Core agents (always active)
orchestrator · strategy_manager · product_strategist · research_liaison ·
debate_architect · evaluation_lead · ethics_lead · compliance_manager · security_specialist

## On-demand agents (routing-triggered)
mlops_strategist · business_analyst · ux_researcher · knowledge_engineer ·
cognitive_scientist · computational_linguist · prompt_engineer · change_manager

## Usage in Claude Code

    /redteam                                              # safety tests first — always
    /debate --scenario data/scenarios/vendor_selection.yaml
    /debate --scenario data/scenarios/risky_use.yaml
    /report                                               # latest report
    /score                                                # latest evaluation scores

## Debate flow

    Rounds 1–4: PRO + CON positions → cross-critiques → on-demand agents → evaluation
    Gates: ethics + compliance + security (parallel) → block = escalation report
    Adjudication → final_result → human report

## Outputs

    reports/<id>_<ts>.md      human report
    sessions/<id>/            all structured agent JSON
    audits/<id>.jsonl         append-only provenance log

## Exit codes

    0 = success, no escalation required
    2 = human review required (gate blocked or escalation flagged)
    1 = fatal error
