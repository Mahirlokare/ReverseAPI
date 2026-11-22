from apiscope.core.static_analysis import extract_routes

def test_static_bundle_route_candidate():
    routes = extract_routes('fetch("/api/v2/users/9"); axios.get("https://service.test/orders/12")')
    assert any(x["path"] == "/api/v2/users/{id}" for x in routes)
    assert any(x["host"] == "service.test" for x in routes)
    assert all(x["source"] == "javascript-static" for x in routes)
