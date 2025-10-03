
def test_identities_and_resolve(client):
    # Create entities
    m = client.post("/members", json={"full_name": "Alice", "primary_email": "alice@example.com"}).json()
    p = client.post("/projects", json={"name": "X", "description": "Proj X"}).json()
    mm = client.post("/meetings", json={"title": "Kickoff"}).json()

    # Add identities
    i1 = client.post("/identities", json={
        "entity_type": "member",
        "entity_id": m["id"],
        "application": "email",
        "external_id": "alice@example.com",
        "display_name": "Alice (email)",
        "is_primary": True
    }).json()

    i2 = client.post("/identities", json={
        "entity_type": "member",
        "entity_id": m["id"],
        "application": "discord",
        "external_id": "1234567890",
        "display_name": "alice#0001"
    }).json()

    # Filter list by entity
    r = client.get("/identities", params={"entity_type": "member", "entity_id": m["id"]})
    assert r.status_code == 200
    identities = r.json()
    assert len(identities) == 2

    # Resolve
    r = client.get(f"/resolve/member/{m['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["entity_type"] == "member"
    assert data["entity"]["full_name"] == "Alice"
    assert len(data["identities"]) == 2

    # Update identity
    r = client.patch(f"/identities/{i2['id']}", json={"display_name": "alice#9999"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "alice#9999"

    # Delete identity
    r = client.delete(f"/identities/{i1['id']}")
    assert r.status_code == 204
