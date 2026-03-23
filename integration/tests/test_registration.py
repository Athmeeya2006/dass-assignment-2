"""Unit tests for registration module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from registration import register_member, get_member, list_members, remove_member


class TestRegisterMember:
    """Test member registration."""

    def test_register_valid_driver(self, reset_store):
        """Register a driver with valid name and role."""
        member = register_member("Ana Torrez", "driver")
        assert member.name == "Ana Torrez"
        assert member.role == "driver"
        assert member.skill_level == 1
        assert member.is_available is True

    def test_register_all_valid_roles(self, reset_store):
        """Register members with all valid roles."""
        roles = ["driver", "mechanic", "strategist", "navigator"]
        for role in roles:
            member = register_member(f"Test {role}", role)
            assert member.role == role

    def test_register_name_too_short(self, reset_store):
        """Name with 1 character should raise ValueError."""
        with pytest.raises(ValueError):
            register_member("A", "driver")

    def test_register_name_two_chars_valid(self, reset_store):
        """Name with 2 characters should be valid (boundary)."""
        member = register_member("AB", "driver")
        assert member.name == "AB"

    def test_register_name_fifty_chars_valid(self, reset_store):
        """Name with 50 characters should be valid (boundary)."""
        name_50 = "A" * 50
        member = register_member(name_50, "driver")
        assert member.name == name_50

    def test_register_name_too_long(self, reset_store):
        """Name with 51 characters should raise ValueError."""
        name_51 = "A" * 51
        with pytest.raises(ValueError):
            register_member(name_51, "driver")

    def test_register_invalid_role(self, reset_store):
        """Invalid role should raise ValueError."""
        with pytest.raises(ValueError):
            register_member("Bob", "invalid_role")

    def test_register_same_name_twice_allowed(self, reset_store):
        """Two members with same name should be allowed (creates separate IDs)."""
        member1 = register_member("Same Name", "driver")
        member2 = register_member("Same Name", "mechanic")
        assert member1.member_id != member2.member_id
        assert member1.name == member2.name


class TestGetMember:
    """Test member retrieval."""

    def test_get_member_valid_id(self, reset_store):
        """Retrieve registered member by valid ID."""
        registered = register_member("Ana Torrez", "driver")
        retrieved = get_member(registered.member_id)
        assert retrieved.member_id == registered.member_id
        assert retrieved.name == "Ana Torrez"

    def test_get_member_invalid_id_raises_keyerror(self, reset_store):
        """Retrieve with invalid ID should raise KeyError."""
        with pytest.raises(KeyError):
            get_member("nonexistent-id")


class TestListMembers:
    """Test member listing."""

    def test_list_members_empty(self, reset_store):
        """List members when none registered."""
        members = list_members()
        assert members == []

    def test_list_members_returns_all(self, reset_store):
        """List should return all registered members."""
        member1 = register_member("Ana", "driver")
        member2 = register_member("Bob", "mechanic")
        member3 = register_member("Cam", "strategist")

        members = list_members()
        assert len(members) == 3
        ids = [m.member_id for m in members]
        assert member1.member_id in ids
        assert member2.member_id in ids
        assert member3.member_id in ids


class TestRemoveMember:
    """Test member removal."""

    def test_remove_member_valid_id(self, reset_store):
        """Remove registered member by valid ID."""
        member = register_member("Ana Torrez", "driver")
        result = remove_member(member.member_id)
        assert result is True
        assert len(list_members()) == 0

    def test_remove_member_invalid_id_raises_keyerror(self, reset_store):
        """Remove with invalid ID should raise KeyError."""
        with pytest.raises(KeyError):
            remove_member("nonexistent-id")

    def test_remove_member_makes_unavailable(self, reset_store):
        """After removal, member should not be retrievable."""
        member = register_member("Ana Torrez", "driver")
        remove_member(member.member_id)
        with pytest.raises(KeyError):
            get_member(member.member_id)
