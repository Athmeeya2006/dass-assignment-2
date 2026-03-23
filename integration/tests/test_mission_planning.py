"""Unit tests for mission_planning module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from mission_planning import (
    create_mission, assign_mission, complete_mission, fail_mission, get_mission
)
from registration import register_member, get_member
from crew_management import set_availability


class TestCreateMission:
    """Test mission creation."""

    def test_create_mission_delivery_valid(self, reset_store):
        """Create delivery mission with valid parameters."""
        mission = create_mission("Package Delivery", "delivery", ["driver", "navigator"])
        assert mission.name == "Package Delivery"
        assert mission.mission_type == "delivery"
        assert mission.required_roles == ["driver", "navigator"]
        assert mission.status == "planned"
        assert mission.assigned_members == []
        assert mission.requires_mechanic is False

    def test_create_mission_rescue_valid(self, reset_store):
        """Create rescue mission with valid parameters."""
        mission = create_mission("Rescue Op", "rescue", ["driver", "mechanic"])
        assert mission.mission_type == "rescue"

    def test_create_mission_surveillance_valid(self, reset_store):
        """Create surveillance mission with valid parameters."""
        mission = create_mission("Spy Op", "surveillance", ["driver", "strategist"])
        assert mission.mission_type == "surveillance"

    def test_create_mission_invalid_type_fails(self, reset_store):
        """Invalid mission type should raise ValueError."""
        with pytest.raises(ValueError):
            create_mission("Bad", "invalid_type", ["driver"])

    def test_create_mission_empty_required_roles_fails(self, reset_store):
        """Empty required_roles should raise ValueError."""
        with pytest.raises(ValueError):
            create_mission("Bad", "delivery", [])

    def test_create_mission_invalid_role_in_required_fails(self, reset_store):
        """Invalid role in required_roles should raise ValueError."""
        with pytest.raises(ValueError):
            create_mission("Bad", "delivery", ["driver", "invalid_role"])

    def test_create_mission_with_damaged_car(self, reset_store):
        """Create mission involving damaged car should require mechanic."""
        mission = create_mission("Repair Mission", "delivery", ["driver"], involves_damaged_car=True)
        assert mission.requires_mechanic is True

    def test_create_mission_without_damaged_car(self, reset_store):
        """Mission without damaged car should not require mechanic."""
        mission = create_mission("Normal Mission", "delivery", ["driver"], involves_damaged_car=False)
        assert mission.requires_mechanic is False


class TestAssignMission:
    """Test mission assignment."""

    def test_assign_mission_single_role_success(self, reset_store, registered_driver):
        """Assign mission with available required role."""
        mission = create_mission("Test", "delivery", ["driver"])
        result = assign_mission(mission.mission_id)
        assert result.status == "active"
        assert len(result.assigned_members) == 1
        assert registered_driver.member_id in result.assigned_members

    def test_assign_mission_multiple_roles_success(self, reset_store, registered_driver, registered_mechanic):
        """Assign mission with multiple required roles."""
        mission = create_mission("Test", "delivery", ["driver", "mechanic"])
        result = assign_mission(mission.mission_id)
        assert result.status == "active"
        assert len(result.assigned_members) == 2

    def test_assign_mission_no_available_driver_fails(self, reset_store):
        """Assign mission when no driver available should raise ValueError."""
        mission = create_mission("Test", "delivery", ["driver"])
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "driver" in str(exc_info.value).lower()

    def test_assign_mission_no_available_mechanic_fails(self, reset_store, registered_driver):
        """Assign mission when no mechanic available should raise ValueError."""
        mission = create_mission("Test", "delivery", ["driver"], involves_damaged_car=True)
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "mechanic" in str(exc_info.value).lower()

    def test_assign_mission_marks_unavailable(self, reset_store, registered_driver):
        """Assign mission should mark assigned members as unavailable."""
        mission = create_mission("Test", "delivery", ["driver"])
        assert registered_driver.is_available is True
        assign_mission(mission.mission_id)
        driver_after = get_member(registered_driver.member_id)
        assert driver_after.is_available is False

    def test_assign_mission_does_not_duplicate_members(self, reset_store):
        """Mission with duplicate role requirements needs multiple members."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        # Mission requiring two drivers
        mission = create_mission("Odd Mission", "delivery", ["driver", "driver"])
        
        # Should succeed with two available drivers
        result = assign_mission(mission.mission_id)
        assert len(result.assigned_members) == 2
        assert driver1.member_id in result.assigned_members or driver2.member_id in result.assigned_members


class TestCompleteMission:
    """Test mission completion."""

    def test_complete_mission_marks_status_completed(self, reset_store, registered_driver):
        """Complete mission should set status to completed."""
        mission = create_mission("Test", "delivery", ["driver"])
        assigned = assign_mission(mission.mission_id)
        result = complete_mission(assigned.mission_id)
        assert result.status == "completed"

    def test_complete_mission_frees_assigned_crew(self, reset_store, registered_driver):
        """Complete mission should mark all assigned crew as available."""
        mission = create_mission("Test", "delivery", ["driver"])
        assign_mission(mission.mission_id)
        assert get_member(registered_driver.member_id).is_available is False

        complete_mission(mission.mission_id)
        assert get_member(registered_driver.member_id).is_available is True

    def test_complete_mission_frees_multiple_crew(self, reset_store, registered_driver, registered_mechanic):
        """Complete mission frees all assigned crew members."""
        mission = create_mission("Test", "delivery", ["driver", "mechanic"])
        assign_mission(mission.mission_id)

        assert get_member(registered_driver.member_id).is_available is False
        assert get_member(registered_mechanic.member_id).is_available is False

        complete_mission(mission.mission_id)

        assert get_member(registered_driver.member_id).is_available is True
        assert get_member(registered_mechanic.member_id).is_available is True


class TestFailMission:
    """Test mission failure."""

    def test_fail_mission_marks_status_failed(self, reset_store, registered_driver):
        """Fail mission should set status to failed."""
        mission = create_mission("Test", "delivery", ["driver"])
        assign_mission(mission.mission_id)
        result = fail_mission(mission.mission_id, "Engine failure")
        assert result.status == "failed"

    def test_fail_mission_frees_assigned_crew(self, reset_store, registered_driver):
        """Fail mission should mark all assigned crew as available."""
        mission = create_mission("Test", "delivery", ["driver"])
        assign_mission(mission.mission_id)
        assert get_member(registered_driver.member_id).is_available is False

        fail_mission(mission.mission_id, "Accident")
        assert get_member(registered_driver.member_id).is_available is True


class TestGetMission:
    """Test mission retrieval."""

    def test_get_mission_valid_id(self, reset_store):
        """Retrieve mission by valid ID."""
        created = create_mission("Test", "delivery", ["driver"])
        retrieved = get_mission(created.mission_id)
        assert retrieved.mission_id == created.mission_id
        assert retrieved.name == "Test"

    def test_get_mission_invalid_id_raises_keyerror(self, reset_store):
        """Retrieve with invalid ID should raise KeyError."""
        with pytest.raises(KeyError):
            get_mission("nonexistent-id")


class TestMissionIntegrationRules:
    """Test complex mission scenarios combining multiple rules."""

    def test_mission_with_damaged_car_requires_available_mechanic(self, reset_store, registered_driver, registered_mechanic):
        """Mission with damaged car fails if mechanic not available."""
        set_availability(registered_mechanic.member_id, False)
        mission = create_mission("Damaged Car", "delivery", ["driver"], involves_damaged_car=True)
        
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "mechanic" in str(exc_info.value).lower()

    def test_mission_role_reassignment_not_same_person(self, reset_store):
        """Mission requiring duplicate roles fails with insufficient members."""
        driver = register_member("Driver", "driver")
        mission = create_mission("Double Driver", "delivery", ["driver", "driver"])
        
        # Should fail because only one driver available
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "driver" in str(exc_info.value).lower()
