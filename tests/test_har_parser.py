from apiscope.core.har_parser import normalize_path, parse_har

def test_numeric_ids_cluster():
    assert normalize_path("/users/42/orders/100") == "/users/{id}/orders/{id}"

def test_uuid_cluster():
    assert normalize_path("/records/123e4567-e89b-12d3-a456-426614174000") == "/records/{id}"

def test_grouping_and_noise_filtering():
    har = {"log": {"entries": [{"request": {"method": "GET", "url": "https://demo.test/users/12"}, "response": {"status": 200}}, {"request": {"method": "GET", "url": "https://demo.test/users/99"}, "response": {"status": 200}}, {"request": {"method": "POST", "url": "https://demo.test/users"}, "response": {"status": 201}}, {"request": {"method": "GET", "url": "https://demo.test/assets/app.js"}, "response": {"status": 200}}]}}
    results = parse_har(har)
    assert len(results) == 2
    user_endpoint = next(x for x in results if x.path_template == "/users/{id}")
    assert user_endpoint.observations == 2
    assert user_endpoint.status_codes == (200,)

def test_invalid_scheme_skipped():
    har = {"log": {"entries": [{"request": {"method": "GET", "url": "file:///tmp/test"}, "response": {"status": 200}}]}}
    assert parse_har(har) == []
