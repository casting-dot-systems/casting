from __future__ import annotations
import uuid

from sqlalchemy import text
from identity_server.db import session_scope
from identity_server import models


def run():
    """Seed example data for testing the identity server."""
    with session_scope() as db:
        # Create a member in catalog schema
        alice_id = uuid.uuid4()
        db.execute(
            text("INSERT INTO catalog.members (member_id, name, status) VALUES (:id, :name, :status)"),
            {"id": str(alice_id), "name": "Alice Example", "status": "active"},
        )

        # Create a project in catalog schema
        proj_id = uuid.uuid4()
        db.execute(
            text("INSERT INTO catalog.projects (id, name, description) VALUES (:id, :name, :desc)"),
            {"id": str(proj_id), "name": "Cast Platform", "desc": "Core platform project"},
        )

        # Create a meeting in catalog schema
        meet_id = uuid.uuid4()
        db.execute(
            text("INSERT INTO catalog.meetings (id, title) VALUES (:id, :title)"),
            {"id": str(meet_id), "title": "Kickoff"},
        )

        # Flush to ensure entities exist
        db.flush()

        # Create application identities
        db.add_all(
            [
                models.ApplicationIdentity(
                    entity_type="member",
                    entity_id=alice_id,
                    application="email",
                    external_id="alice@example.com",
                    display_name="Alice (email)",
                    is_primary=True,
                ),
                models.ApplicationIdentity(
                    entity_type="member",
                    entity_id=alice_id,
                    application="discord",
                    external_id="1234567890",
                    display_name="alice#0001",
                    metadata={"server": "cast"},
                ),
                models.ApplicationIdentity(
                    entity_type="project",
                    entity_id=proj_id,
                    application="notion",
                    external_id="abcd1234",
                    uri="https://notion.so/some-page",
                ),
                models.ApplicationIdentity(
                    entity_type="meeting",
                    entity_id=meet_id,
                    application="obsidian",
                    external_id="2024-01-01-kickoff",
                    uri="obsidian://open?vault=cast&file=kickoff",
                ),
            ]
        )

        print("Seeded example data:")
        print(f" member: {alice_id}")
        print(f" project: {proj_id}")
        print(f" meeting: {meet_id}")


if __name__ == "__main__":
    run()
