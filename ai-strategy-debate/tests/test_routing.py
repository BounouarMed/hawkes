import pytest

def make_turn(position="pro", security_concern=False, unverified=False):
    claims = [{"claim_id":"c1","text":"Claim.","evidence_status":"plausible"}]
    if unverified:
        claims.append({"claim_id":"c2","text":"Risky.","evidence_status":"unverified"})
    return {
        "scenario_id":"t01","phase":"x","round":1,"agent":"product_strategist","position":position,
        "claims":claims,"steelman_of_opposing":"The opposing view has merit.",
        "weaknesses":["W1"],"uncertainties":[],"on_demand_requests":[],
        "security_concern":security_concern,"confidence":0.7,
    }

def setup_router(tmp_path, monkeypatch, risk_level="medium"):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "routing.yaml").write_text("rules: []")
    from src.session_ledger import SessionLedger
    from src.router import Router
    scenario = {"question":"q","constraints":{"risk_level":risk_level}}
    ledger = SessionLedger("test")
    return Router(scenario, ledger)

def test_security_triggers_mlops(tmp_path, monkeypatch):
    router = setup_router(tmp_path, monkeypatch)
    triggered = router._evaluate_rules(1, {"a": make_turn(security_concern=True)}, {})
    assert "mlops_strategist" in triggered

def test_unverified_triggers_knowledge_engineer(tmp_path, monkeypatch):
    router = setup_router(tmp_path, monkeypatch)
    triggered = router._evaluate_rules(1, {"a": make_turn(unverified=True)}, {})
    assert "knowledge_engineer" in triggered

def test_high_risk_triggers_cognitive_scientist(tmp_path, monkeypatch):
    router = setup_router(tmp_path, monkeypatch, risk_level="high")
    triggered = router._evaluate_rules(1, {}, {})
    assert "cognitive_scientist" in triggered
