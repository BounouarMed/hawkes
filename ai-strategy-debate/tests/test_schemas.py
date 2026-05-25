import json
from pathlib import Path
import pytest
import jsonschema

SCHEMA_DIR = Path("schemas")

VALID = {
    "debate_turn": {
        "scenario_id":"t01","phase":"initial","round":1,"agent":"product_strategist",
        "position":"pro",
        "claims":[{"claim_id":"c1","text":"Vendor A reduces TTM.","evidence_status":"plausible"}],
        "steelman_of_opposing":"The opposing view argues that data control justifies higher cost.",
        "weaknesses":["Vendor lock-in not resolved."],
        "uncertainties":["Contract terms TBD."],
        "on_demand_requests":[],"confidence":0.7,
    },
    "ethics_verdict": {
        "gate_result":"pass","issues_found":[],"pii_detected":False,
        "manipulation_risk":"none","prohibited_practice":False,
    },
    "security_verdict": {
        "gate_result":"pass","threats_found":[],"injection_detected":False,"exfiltration_risk":"none",
    },
    "compliance_verdict": {
        "gate_result":"pass","legal_basis_present":True,"gdpr_concern":False,"ai_act_concern":False,"flags":[],
    },
    "final_result": {
        "scenario_id":"t01","verdict":"conditional_recommend","winning_position":"hybrid",
        "rationale":["Better risk balance."],"blocking_issues":[],"conditions":["Resolve reversibility."],
        "human_escalation_required":False,
    },
}

INVALID = {
    "debate_turn": {
        "scenario_id":"t01","phase":"x","round":0,"agent":"x","position":"invalid",
        "claims":[],"steelman_of_opposing":"short","weaknesses":[],"uncertainties":[],
        "on_demand_requests":[],"confidence":1.5,
    },
}

def load_schema(name):
    candidates = list(SCHEMA_DIR.glob(f"{name}*.json"))
    assert candidates, f"No schema for {name}"
    return json.loads(candidates[0].read_text())

@pytest.mark.parametrize("name,data", list(VALID.items()))
def test_valid(name, data):
    jsonschema.validate(instance=data, schema=load_schema(name))

@pytest.mark.parametrize("name,data", list(INVALID.items()))
def test_invalid(name, data):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=load_schema(name))
