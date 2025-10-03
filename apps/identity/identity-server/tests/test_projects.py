
def test_project_crud(client):
    r = client.post("/projects", json={"name": "Cast", "description": "Platform"})
    assert r.status_code == 201
    proj = r.json()

    r = client.get(f"/projects/{proj['id']}")
    assert r.status_code == 200

    r = client.get("/projects")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.patch(f"/projects/{proj['id']}", json={"name": "Cast 2"})
    assert r.status_code == 200
    assert r.json()["name"] == "Cast 2"

    r = client.delete(f"/projects/{proj['id']}")
    assert r.status_code == 204
