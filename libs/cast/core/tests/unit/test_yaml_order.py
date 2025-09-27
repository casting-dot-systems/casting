"""Tests for the new YAML ordering and canonicalization."""

from casting.cast.core.yamlio import reorder_cast_fields

def test_reorder_groups_and_positions():
    fm = {
        "title": "Note",
        "cast-zzz": "z",
        "last-updated": "2025-09-01T10:00:00-07:00",
        "foo": 1,
        "cast-version": 3,
        "cast-id": "abc-123",
        "cast-hsync": ["B (watch)", "A (live)", "B (watch)"],
        "cast-codebases": ["core", "core", "alpha"],
    }

    out = reorder_cast_fields(fm)
    keys = list(out.keys())

    # 1) last-updated first
    assert keys[0] == "last-updated"

    # 2) cast-id immediately after
    assert keys[1] == "cast-id"

    # Collect cast-* block
    cast_block = [k for k in keys if k.startswith("cast-")]

    # 3) Ensure cast-version is last within cast-* block
    assert cast_block[-1] == "cast-version"

    # 4) Ensure other cast-* keys (including unknown) are between id and version
    assert "cast-hsync" in cast_block
    assert "cast-codebases" in cast_block
    assert "cast-zzz" in cast_block
    assert cast_block.index("cast-id") < cast_block.index("cast-zzz") < cast_block.index("cast-version")

    # 5) Non-cast fields follow after the cast block
    tail = keys[keys.index("cast-version") + 1 :]
    assert "title" in tail and "foo" in tail

    # Canonicalization of lists
    assert out["cast-hsync"] == ["A (live)", "B (watch)"]  # dedup + alpha by name, live preferred
    assert out["cast-codebases"] == ["alpha", "core"]      # dedup + alpha


def test_reorder_empty_front_matter():
    """Test reordering with empty or None front matter."""
    assert reorder_cast_fields({}) == {}
    assert reorder_cast_fields(None) == {}


def test_reorder_no_cast_fields():
    """Test reordering with no cast-* fields."""
    fm = {
        "title": "Regular Note",
        "author": "Someone",
        "last-updated": "2025-09-01T10:00:00-07:00",
    }

    out = reorder_cast_fields(fm)
    keys = list(out.keys())

    # last-updated should be first
    assert keys[0] == "last-updated"
    # other fields follow in original order
    assert keys[1:] == ["title", "author"]


def test_reorder_known_cast_keys_ordering():
    """Test that known cast keys appear in the correct order."""
    fm = {
        "cast-version": 1,
        "cast-codebases": ["beta", "alpha"],
        "cast-hsync": ["Z (watch)", "A (live)"],
        "cast-id": "test-id",
        "last-updated": "2025-09-01T10:00:00-07:00",
    }

    out = reorder_cast_fields(fm)
    keys = list(out.keys())

    expected_order = [
        "last-updated",
        "cast-id",
        "cast-hsync",      # known key
        "cast-codebases",  # known key
        "cast-version"
    ]

    assert keys == expected_order


def test_reorder_unknown_cast_keys():
    """Test that unknown cast-* keys are sorted alphabetically between known keys and cast-version."""
    fm = {
        "cast-version": 1,
        "cast-zebra": "z",
        "cast-apple": "a",
        "cast-id": "test-id",
        "last-updated": "2025-09-01T10:00:00-07:00",
        "cast-hsync": ["A (live)"],
    }

    out = reorder_cast_fields(fm)
    keys = list(out.keys())

    expected_order = [
        "last-updated",
        "cast-id",
        "cast-hsync",      # known key first
        "cast-apple",      # unknown keys alphabetically
        "cast-zebra",
        "cast-version"     # version last
    ]

    assert keys == expected_order


def test_reorder_preserves_non_cast_field_order():
    """Test that non-cast fields maintain their original order."""
    fm = {
        "zebra": "z",
        "cast-id": "test-id",
        "apple": "a",
        "cast-version": 1,
        "banana": "b",
        "last-updated": "2025-09-01T10:00:00-07:00",
    }

    out = reorder_cast_fields(fm)

    # Find where non-cast fields start (after cast-version)
    keys = list(out.keys())
    version_index = keys.index("cast-version")
    non_cast_fields = keys[version_index + 1:]

    # Should preserve original order: zebra, apple, banana
    expected_non_cast_order = ["zebra", "apple", "banana"]
    assert non_cast_fields == expected_non_cast_order


def test_canonicalize_cast_hsync():
    """Test cast-hsync canonicalization."""
    fm = {
        "cast-id": "test-id",
        "cast-hsync": ["B (watch)", "A (live)", "B (live)", "A (watch)"],
        "cast-version": 1,
    }

    out = reorder_cast_fields(fm)

    # Should dedup and prefer live, then sort alphabetically
    assert out["cast-hsync"] == ["A (live)", "B (live)"]


def test_canonicalize_cast_codebases():
    """Test cast-codebases canonicalization."""
    fm = {
        "cast-id": "test-id",
        "cast-codebases": ["gamma", "alpha", "beta", "alpha"],
        "cast-version": 1,
    }

    out = reorder_cast_fields(fm)

    # Should dedup and sort alphabetically
    assert out["cast-codebases"] == ["alpha", "beta", "gamma"]