import json
from apiscope.core.mvp_analysis import parse_har, summarize, export_openapi, compare_scans, make_tests

def fixture():
    return {"log":{"entries":[
      {"request":{"method":"GET","url":"https://api.demo/users/7?api_key=secret","headers":[{"name":"Authorization","value":"Bearer private"}]},
       "response":{"status":200,"content":{"mimeType":"application/json","text":"{\\"id\\":7,\\"name\\":\\"Demo\\",\\"password\\":\\"hidden\\"}"}}},
      {"request":{"method":"GET","url":"https://api.demo/users/8"},"response":{"status":200,"content":{"mimeType":"application/json","text":"{\\"id\\":8,\\"name\\":\\"Sample\\"}"}}}
    ]}}

def scan_fixture():
    return summarize(parse_har(fixture()))

def test_parser_groups_routes_and_redacts():
    scan=scan_fixture()
    assert scan["endpoint_count"]==1
    endpoint=scan["endpoints"][0]
    assert endpoint["path"]=="/users/{id}" and endpoint["observations"]==2
    assert "secret" not in endpoint["sample_urls"][0]
    assert "password" not in endpoint["response_schema"].get("properties",{})

def test_openapi_export():
    spec=export_openapi(scan_fixture())
    assert spec["openapi"]=="3.1.0" and "/users/{id}" in spec["paths"]

def test_generated_pytest_snapshot():
    code=make_tests(scan_fixture())
    assert "def test_route_0_exists" in code and "SCAN" in code

def test_diff_detects_added_routes():
    diff=compare_scans({"endpoints":[]},scan_fixture())
    assert diff["summary"]["added"]==1
