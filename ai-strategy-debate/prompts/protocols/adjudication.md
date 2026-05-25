<adjudication_protocol>
Orchestrator reads: all turns, all critiques, evaluation scorecard(s),
ethics verdict, compliance verdict, security verdict, on-demand contributions.

Weighting rules:
1. blocked gates override all → automatic escalate verdict
2. blocking_issues from any gate appear in final_result.blocking_issues
3. Evidence quality (eval score) weights each position's confidence
4. Unresolved claims downgrade winning_position confidence
5. human_escalation_required=true if:
   - any gate returned pass_with_warnings AND risk_level=high
   - evaluation_lead requested >2 additional rounds
   - any agent confidence < 0.4
   - any blocking_issue remains unresolved

Output: final_result JSON conforming to final_result.schema.json
</adjudication_protocol>
