"""Unit tests for crew_management module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from crew_management import (
    assign_role, update_skill_level, set_availability, get_available_by_role
)
from registration import register_member


class TestAssignRole:
    """Test role assignment."""

    def test_assign_role_valid_to_registered_member(self, reset_store):
        """Assign role to registered member."""
        member = register_member("Ana", "driver")
        updated = assign_role(member.member_id, "mechanic")
        assert updated.role == "mechanic"

    def test_assign_role_to_unregistered_member(self, reset_store):
        """Assign role to non-existent member should raise KeyError."""
        with pytest.raises(KeyError):
            assign_role("nonexistent-id", "driver")

    def test_assign_role_invalid_role(self, reset_store):
        """Assign invalid role should raise ValueError."""
        member = register_member("Ana", "driver")
        with pytest.raises(ValueError):
            assign_role(member.member_id, "invalid_role")

    def test_assign_role_all_valid_transitions(self, reset_store):
        """Assign each valid role (transitions)."""
        member = register_member("Ana", "driver")
        roles = ["driver", "mechanic", "strategist", "navigator"]
        for role in roles:
            updated = assign_role(member.member_id, role)
            assert updated.role == role


class TestUpdateSkillLevel:
    """Test skill level updates."""

    def test_update_skill_level_valid(self, reset_store):
        """Update skill level to valid value."""
        member = register_member("Ana", "driver")
        updated = update_skill_level(member.member_id, 5)
        assert updated.skill_level == 5

    def test_update_skill_level_boundary_1(self, reset_store):
        """Update skill level to 1 (minimum boundary)."""
        member = register_member("Ana", "driver")
        updated = update_skill_level(member.member_id, 1)
        assert updated.skill_level == 1

    def test_update_skill_level_boundary_10(self, reset_store):
        """Update skill level to 10 (maximum boundary)."""
        member = register_member("Ana", "driver")
        updated = update_skill_level(member.member_id, 10)
        assert updated.skill_level == 10

    def test_update_skill_level_zero_raises_error(self, reset_store):
        """Skill level 0 should raise ValueError."""
        member = register_member("Ana", "driver")
        with pytest.raises(ValueError):
            update_skill_level(member.member_id, 0)

    def test_update_skill_level_11_raises_error(self, reset_store):
        """Skill level 11 should raise ValueError."""
        member = register_member("Ana", "driver")
        with pytest.raises(ValueError):
            update_skill_level(member.member_id, 11)

    def test_update_skill_level_nonexistent_member(self, reset_store):
        """Update skill level for non-existent member should raise KeyError."""
        with pytest.raises(KeyError):
            update_skill_level("nonexistent-id", 5)


class TestSetAvailability:
    """Test availability management."""

    def test_set_available_true(self, reset_store):
        """Set member as available."""
        member = register_member("Ana", "driver")
        updated = set_availability(member.member_id, True)
        assert updated.is_available is True

    def test_set_available_false(self, reset_store):
        """Set member as unavailable."""
        member = register_member("Ana", "driver")
        updated = set_availability(member.member_id, False)
        assert updated.is_available is False

    def test_set_availability_nonexistent_member(self, reset_store):
        """Set availability for non-existent member should raise KeyError."""
        with pytest.raises(KeyError):
            set_availability("nonexistent-id", True)


class TestGetAvailableByRole:
    """Test filtering available members by role."""

    def test_get_available_by_role_empty(self, reset_store):
        """Get available role when none registered."""
        result = get_available_by_role("driver")
        assert result == []

    def test_get_available_by_role_returns_only_available(self, reset_store):
        """Get available should exclude unavailable members."""
        driver1 = register_member("Ana", "driver")
        driver2 = register_member("Bob", "driver")
        set_availability(driver1.member_id, False)

        available = get_available_by_role("driver")
        assert len(available) == 1
        assert available[0].member_id == driver2.member_id

    def test_get_available_by_role_returns_only_matching_role(self, reset_store):
        """Get available should exclude different roles."""
        driver = register_member("Ana", "driver")
        mechanic = register_member("Bob", "mechanic")

        drivers = get_available_by_role("driver")
        assert len(drivers) == 1
        assert drivers[0].member_id == driver.member_id

        mechanics = get_available_by_role("mechanic")
        assert len(mechanics) == 1
        assert mechanics[0].member_id == mechanic.member_id

    def test_get_available_by_role_multiple_available(self, reset_store):
        """Get available should return multiple matching available members."""
        driver1 = register_member("Ana", "driver")
        driver2 = register_member("Bob", "driver")
        driver3 = register_member("Cam", "driver")

        available = get_available_by_role("driver")
        assert len(available) == 3
        ids = [m.member_id for m in available]
        assert driver1.member_id in ids
        assert driver2.member_id in ids
        assert driver3.member_id in ids
