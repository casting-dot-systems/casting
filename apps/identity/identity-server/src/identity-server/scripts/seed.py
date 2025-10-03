
from __future__ import annotations
import uuid

from app.db import session_scope
from app import models


def run():
    with session_scope() as db:
        # Member
        alice = models.Member(full_name="Alice Example", primary_email="alice@example.com")
        db.add(alice)
        db.flush()

        # Project
        proj = models.Project(name="Cast Platform", description="Core platform project")
        db.add(proj)
        db.flush()

        # Meeting
        meet = models.Meeting(title="Kickoff")
        db.add(meet)
        db.flush()

        # Identities
        db.add_all(
            [
                models.ApplicationIdentity(
                    entity_type="member",
                    entity_id=alice.id,
                    application="email",
                    external_id="alice@example.com",
                    display_name="Alice (email)",
                    is_primary=True,
                ),
                models.ApplicationIdentity(
                    entity_type="member",
                    entity_id=alice.id,
                    application="discord",
                    external_id="1234567890",
                    display_name="alice#0001",
                    metadata={"server": "cast"},
                ),
                models.ApplicationIdentity(
                    entity_type="project",
                    entity_id=proj.id,
                    application="notion",
                    external_id="abcd1234",
                    uri="https://notion.so/some-page",
                ),
                models.ApplicationIdentity(
                    entity_type="meeting",
                    entity_id=meet.id,
                    application="obsidian",
                    external_id="2024-01-01-kickoff",
                    uri="obsidian://open?vault=cast&file=kickoff",
                ),
            ]
        )
        print("Seeded example data:")
        print(" member:", alice.id)
        print(" project:", proj.id)
        print(" meeting:", meet.id)


if __name__ == "__main__":
    run()
