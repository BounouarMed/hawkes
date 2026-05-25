<escalation_protocol>
Triggered when: any gate blocks OR human_escalation_required=true

Write escalation report to: reports/<scenario_id>_ESCALATION_<timestamp>.md

Report must contain:
- Which gate(s) blocked and why
- The specific blocking issues and which agent raised them
- What evidence was cited
- What the human reviewer must decide
- Which documents need DPO or legal review

Exit code 2. No recommendation released.
Session ledger and audit log preserved in full.
</escalation_protocol>
