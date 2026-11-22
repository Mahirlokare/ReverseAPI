from apiscope.main import analyze, export_openapi, generate_tests, compare
import json

def fixture():
    return {"log":{"entries":[
      {"request":{"method":"GET","url":"https://api.demo/users/7?api_key=secret","headers":[{"name":"Authorization","value":"Bearer private"}]},
       "response":{"status":200,"content":{"mimeType":"application/json","text":"{\"id\":7,\"name\":\"Demo\",\"password\":\"hidden\"}"}}},
      {"request":{"method":"GET","url":"https://api.demo/users/8"},"response":{"status":200,"content":{"mimeType":"application/json","text":"{\"id\":8,\"name\":\"Sample\"}"}}}
    ]}}

def test_har_analysis_groups_and_redacts():
    scan=analyze(json.dumps(fixture()).encode(),"capture.har")
    assert scan["endpoint_count"]==1
    ep=scan["endpoints"][0]
    assert ep["path"]=="/users/{id}"
    assert ep["observations"]==2
    assert "secret" not in ep["sample_urls"][0]
    assert "password" not in ep["response_schema"].get("properties",{})

def test_openapi_export_structure():
    scan=analyze(json.dumps(fixture()).encode(),"capture.har")
    spec=export_openapi(scan)
    assert spec["openapi"]=="3.1.0" and "/users/{id}" in spec["paths"]

def test_offline_tests_are_returned():
    scan=analyze(json.dumps(fixture()).encode(),"capture.har")
    generated=generate_tests(scan)
    assert generated["filename"].endswith(".py")
    assert "def test_route_0_present" in generated["content"]

def test_drift_compare_finds_additions():
    scan=analyze(json.dumps(fixture()).encode(),"capture.har")
    empty={"endpoints":[]}
    result=compare({"before":empty,"after":scan})
    assert result["summary"]["added"]==1
