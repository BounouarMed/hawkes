Show evaluation scorecards for the most recent debate session.

Usage: /score [session-id]

Steps:
1. Find most recent session in sessions/ (or use provided session-id).
2. Read all evaluation_r*.json files from that session.
3. Print score table: evidence_quality, argument_charity, claim_coverage,
   uncertainty_honesty, steelman_quality.
4. List contradictions and unresolved claims.
