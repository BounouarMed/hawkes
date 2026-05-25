Run a full AI strategy debate simulation.

Usage: /debate --scenario <path>

Examples:
  /debate --scenario data/scenarios/vendor_selection.yaml
  /debate --scenario data/scenarios/risky_use.yaml
  /debate --scenario data/scenarios/inter_bu_arbitration.yaml

Steps:
1. Run: python src/orchestrator.py --scenario <path>
2. Monitor progress. The system runs 1–4 debate rounds automatically.
3. Report saved to reports/ when complete.
4. Exit code 2 = human review required. Alert the user.

Cost estimates:
  vendor_selection (medium): $0.50–1.50
  risky_use (critical, likely blocks): $0.30–0.80
  inter_bu_arbitration (high, 3+ agents): $1.00–2.50
  policy_review (low): $0.20–0.60
