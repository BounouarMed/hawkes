def test_schema_rejects_bad_turn():
    from src.schema_validator import is_valid
    assert not is_valid({"scenario_id":"x","confidence":2.0}, "debate_turn")

def test_ledger_pattern(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from src.session_ledger import SessionLedger
    ledger = SessionLedger("loop_test")
    ledger.write("turns/product_strategist_r1", {"round":1})
    ledger.write("turns/research_liaison_r1", {"round":1})
    ledger.write("evaluation_r1", {"round":1,"scores":{}})
    assert len(ledger.read_pattern("turns__*")) == 2
    assert len(ledger.read_pattern("evaluation_r*")) == 1

def test_provenance_jsonl(tmp_path, monkeypatch):
    import json
    monkeypatch.chdir(tmp_path)
    from src.provenance import ProvenanceLog
    prov = ProvenanceLog("test_prov")
    prov.record("test_event","orchestrator",{"key":"value"})
    lines = prov._path.read_text().strip().split("\n")
    entry = json.loads(lines[0])
    assert entry["event_type"] == "test_event"
