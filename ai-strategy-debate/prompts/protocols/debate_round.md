<debate_protocol>
PHASE 1 — Initial positions (parallel):
  product_strategist: argue PRO | research_liaison: argue CON
  Both must steelman the opposing position (min 20 words) before arguing their own.

PHASE 2 — Cross-critique (sequential):
  product_strategist critiques research_liaison's turn.
  research_liaison critiques product_strategist's turn.
  Each must identify: strongest point, top 3 weaknesses, minimum correction.

PHASE 3 — On-demand contributions (parallel, if triggered):
  On-demand agents contribute neutral domain perspectives.

PHASE 4 — Evaluation:
  evaluation_lead scores all turns.
  quality_verdict=needs_additional_round → proceed to round N+1 (max 4).

PHASE 5 — Gate review (parallel):
  ethics_lead + compliance_manager + security_specialist.
  Any block halts pipeline immediately.

PHASE 6 — Adjudication:
  orchestrator reads all verdicts, scores, turns. Produces final_result JSON.

PHASE 7 — Report:
  orchestrator writes human-readable markdown report.

Forbidden in all rounds:
  straw-man | false dilemma | emotional appeals as evidence |
  normative pressure as analysis | unlabelled claims
</debate_protocol>
