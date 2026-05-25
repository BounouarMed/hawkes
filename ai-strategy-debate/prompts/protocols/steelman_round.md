<steelman_protocol>
Triggered when evaluation quality is below threshold.
1. Read opposing position's full turn history.
2. Reconstruct the strongest possible version of that position —
   better than the opposing agent argued it themselves.
3. Then rebut it. Engage the strengthened version, not original weaknesses.
4. Update confidence score based on what the steelman revealed.
If steelman < 20 words: debate_architect flags as process violation.
Orchestrator may request a rerun of that agent's turn.
</steelman_protocol>
