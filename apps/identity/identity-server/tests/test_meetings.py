
def test_meeting_crud(client):
    r = client.post("/meetings", json={"title": "Sync"})
    assert r.status_code == 201
    mtg = r.json()

    r = client.get(f"/meetings/{mtg['id']}")
    assert r.status_code == 200

    r = client.get("/meetings")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.patch(f"/meetings/{mtg['id']}", json={"title": "Sync+"})
    assert r.status_code == 200
    assert r.json()["title"] == "Sync+"

    r = client.delete(f"/meetings/{mtg['id']}")
    assert r.status_code == 204
