from enum import StrEnum


class EntityType(StrEnum):
    member = "member"
    meeting = "meeting"
    project = "project"


# This is deliberately *not* an Enum in the DB to keep it flexible.
# Use these constants in code/tests for consistency.
KNOWN_APPLICATIONS = {
    "email",
    "notion",
    "obsidian",
    "discord",
    "slack",
    "github",
    "linear",
    "jira",
}
