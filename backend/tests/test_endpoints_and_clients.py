import pytest
from app.models import APIEndpoint, GeneratedClient, GeneratedClientFile


@pytest.mark.asyncio
async def test_endpoints_and_clients(client, auth_user, db_session):
    headers = auth_user["headers"]
    project_id = auth_user["workspace"].id

    # Create dummy project
    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "E-Commerce API",
            "target_website": "https://store.example.com",
            "workspace_id": str(auth_user["workspace"].id),
            "default_output_language": "python",
            "default_execution_mode": "agent",
        },
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Manually create an endpoint in DB
    endpoint = APIEndpoint(
        project_id=proj_id,
        name="GET /api/v1/catalog",
        method="GET",
        path="/api/v1/catalog",
        full_url="https://store.example.com/api/v1/catalog",
        host="store.example.com",
        status_code=200,
    )
    db_session.add(endpoint)

    # Manually create a generated client in DB
    gen_client = GeneratedClient(
        name="store-api-python-client",
        language="python",
        project_id=proj_id,
        validation_status="passed",
    )
    db_session.add(gen_client)
    await db_session.flush()

    file1 = GeneratedClientFile(
        client_id=gen_client.id,
        file_path="api_client.py",
        file_name="api_client.py",
        content="print('Client ready')",
        size=20,
    )
    db_session.add(file1)
    await db_session.commit()

    # 1. List Endpoints
    ep_res = await client.get(f"/api/v1/endpoints?project_id={proj_id}", headers=headers)
    assert ep_res.status_code == 200
    ep_data = ep_res.json()
    assert ep_data["total"] >= 1
    assert ep_data["items"][0]["path"] == "/api/v1/catalog"

    # 2. List Clients
    cl_res = await client.get(f"/api/v1/clients?project_id={proj_id}", headers=headers)
    assert cl_res.status_code == 200
    cl_data = cl_res.json()
    assert cl_data["total"] >= 1
    client_id = cl_data["items"][0]["id"]

    # 3. Download Client ZIP
    dl_res = await client.get(f"/api/v1/clients/{client_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/zip"
    assert len(dl_res.content) > 0

    # 4. Execute Client
    exec_res = await client.post(
        f"/api/v1/clients/{client_id}/execute?entry_point=api_client.py",
        headers=headers,
        json={"test": True},
    )
    assert exec_res.status_code == 201
    exec_data = exec_res.json()
    assert exec_data["status"] == "completed"
    assert exec_data["exit_code"] == 0
