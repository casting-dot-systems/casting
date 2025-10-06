import uuid
from sqlalchemy import text


def test_create_and_list_identities(client, db_session):
    """Test creating and listing identities."""
    # Create a test member in catalog schema
    member_id = str(uuid.uuid4())
    db_session.execute(
        text("INSERT INTO catalog_members (member_id, name, status) VALUES (:id, :name, :status)"),
        {"id": member_id, "name": "Alice", "status": "active"},
    )
    db_session.commit()

    # Create identity
    response = client.post(
        "/identities",
        json={
            "entity_type": "member",
            "entity_id": member_id,
            "application": "email",
            "external_id": "alice@example.com",
            "display_name": "Alice (email)",
            "is_primary": True,
        },
    )
    assert response.status_code == 201
    identity = response.json()
    assert identity["application"] == "email"
    assert identity["external_id"] == "alice@example.com"

    # List all identities
    response = client.get("/identities")
    assert response.status_code == 200
    identities = response.json()
    assert len(identities) == 1

    # Filter by entity
    response = client.get("/identities", params={"entity_type": "member", "entity_id": member_id})
    assert response.status_code == 200
    identities = response.json()
    assert len(identities) == 1


def test_resolve_member(client, db_session):
    """Test resolving a member with multiple identities."""
    # Create test member
    member_id = str(uuid.uuid4())
    db_session.execute(
        text("INSERT INTO catalog_members (member_id, name, status) VALUES (:id, :name, :status)"),
        {"id": member_id, "name": "Bob", "status": "active"},
    )
    db_session.commit()

    # Create identities
    client.post(
        "/identities",
        json={
            "entity_type": "member",
            "entity_id": member_id,
            "application": "email",
            "external_id": "bob@example.com",
            "display_name": "Bob (email)",
            "is_primary": True,
        },
    )

    client.post(
        "/identities",
        json={
            "entity_type": "member",
            "entity_id": member_id,
            "application": "discord",
            "external_id": "9876543210",
            "display_name": "bob#1234",
        },
    )

    # Resolve member
    response = client.get(f"/resolve/member/{member_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["entity_type"] == "member"
    assert data["entity"]["member_id"] == member_id
    assert data["entity"]["name"] == "Bob"
    assert data["entity"]["status"] == "active"
    assert len(data["identities"]) == 2


def test_update_and_delete_identity(client, db_session):
    """Test updating and deleting identities."""
    # Create test member
    member_id = str(uuid.uuid4())
    db_session.execute(
        text("INSERT INTO catalog_members (member_id, name, status) VALUES (:id, :name, :status)"),
        {"id": member_id, "name": "Charlie", "status": "active"},
    )
    db_session.commit()

    # Create identity
    response = client.post(
        "/identities",
        json={
            "entity_type": "member",
            "entity_id": member_id,
            "application": "notion",
            "external_id": "page123",
            "display_name": "Charlie's Notion",
        },
    )
    identity_id = response.json()["id"]

    # Update identity
    response = client.patch(f"/identities/{identity_id}", json={"display_name": "Updated Notion"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated Notion"

    # Delete identity
    response = client.delete(f"/identities/{identity_id}")
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/identities/{identity_id}")
    assert response.status_code == 404


def test_resolve_nonexistent_entity(client):
    """Test resolving a nonexistent entity returns 404."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/resolve/member/{fake_id}")
    assert response.status_code == 404
