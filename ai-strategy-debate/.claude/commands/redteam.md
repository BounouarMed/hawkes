Run the full red-team and safety test suite. No API calls.

Usage: /redteam

Steps:
1. python -m pytest tests/ -v --tb=short
2. All tests must pass before any live run.
3. Report failures. Do not proceed if any fail.

Covers: schema validation, routing rules, safety invariants,
session ledger integrity, provenance log correctness.
