from apiscope.core.security_lint import lint_scan
from apiscope.core.inference import infer_from_samples,confidence

def test_inference_optional_properties():
    schema=infer_from_samples([{"id":1,"name":"A"},{"id":2,"email":"e"}])
    assert "id" in schema["required"] and "name" not in schema["required"]
def test_confidence_is_bounded():
    assert 0<=confidence(100)<=0.99
def test_passive_linter_findings():
    findings=lint_scan({"endpoints":[{"method":"GET","path":"/profile","status_codes":[500],"auth_signals":[],"response_schema":{"type":"object","properties":{"password":{"type":"string"}}}}]})
    assert any(x["rule"]=="SERVER_ERROR_OBSERVED" for x in findings)
    assert any(x["rule"]=="SENSITIVE_FIELD_NAME" for x in findings)
