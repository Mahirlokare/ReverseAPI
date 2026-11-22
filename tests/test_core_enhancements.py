import json
from apiscope.core.mvp_analysis import infer, merge_schemas, normalize, safe_url

def test_schema_merge_tracks_optional_fields():
    merged = merge_schemas([infer({"id": 1, "name": "x"}), infer({"id": 2, "active": True})])
    assert merged["type"] == "object"
    assert "id" in merged["required"]
    assert "name" not in merged["required"] and "active" not in merged["required"]

def test_array_schema_merge():
    result = merge_schemas([infer([1, 2]), infer([3.5])])
    assert result["type"] == "array"
    assert result["items"]["type"] == ["integer", "number"]

def test_sensitive_query_redaction():
    url = safe_url("https://example.test/search?access_token=secret&term=abc")
    assert "secret" not in url and "REDACTED" in url and "term=abc" in url

def test_path_normalization():
    assert normalize("/v1/users/123/orders/456") == "/v1/users/{id}/orders/{id}"
