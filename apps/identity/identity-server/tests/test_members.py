
def test_member_crud(client):
    # Create
    r = client.post("/members", json={"full_name": "Test User", "primary_email": "test@example.com"})
    assert r.status_code == 201, r.text
    member = r.json()
    mid = member["id"]

    # Read
    r = client.get(f"/members/{mid}")
    assert r.status_code == 200
    assert r.json()["full_name"] == "Test User"

    # List
    r = client.get("/members")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Update
    r = client.patch(f"/members/{mid}", json={"full_name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Renamed"

    # Delete
    r = client.delete(f"/members/{mid}")
    assert r.status_code == 204

    # Not found
    r = client.get(f"/members/{mid}")
    assert r.status_code == 404
