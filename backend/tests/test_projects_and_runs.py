import pytest


@pytest.mark.asyncio
async def test_projects_crud_and_runs(client, auth_user):
    headers = auth_user["headers"]
    workspace_id = str(auth_user["workspace"].id)

    # 1. Create Project
    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Target API Project",
            "target_website": "https://httpbin.org/get",
            "description": "Test target project",
            "workspace_id": workspace_id,
            "default_output_language": "typescript",
            "default_execution_mode": "agent",
        },
    )
    assert proj_res.status_code == 201
    project = proj_res.json()
    project_id = project["id"]
    assert project["name"] == "Target API Project"

    # 2. SSRF Protection: Attempting to target localhost should fail
    ssrf_res = await client.post(
        "/api/v1/runs",
        headers=headers,
        json={
            "project_id": project_id,
            "target_url": "http://127.0.0.1:8080/admin",
            "task": "Extract private keys",
            "mode": "agent",
            "output_language": "typescript",
        },
    )
    assert ssrf_res.status_code == 400
    assert "restricted" in ssrf_res.json()["detail"].lower() or "prohibited" in ssrf_res.json()["detail"].lower()

    # 3. Create Valid Run
    run_res = await client.post(
        "/api/v1/runs",
        headers=headers,
        json={
            "project_id": project_id,
            "target_url": "https://api.example.com/products",
            "task": "Discover the product search API with pagination",
            "mode": "agent",
            "output_language": "typescript",
        },
    )
    assert run_res.status_code == 201
    run = run_res.json()
    run_id = run["id"]
    assert run["status"] in ["queued", "initializing", "browser_starting"]

    # 4. Fetch Run Details
    detail_res = await client.get(f"/api/v1/runs/{run_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == run_id

    # 5. Cancel Run
    cancel_res = await client.post(f"/api/v1/runs/{run_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
