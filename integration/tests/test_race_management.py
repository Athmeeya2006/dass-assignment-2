"""Unit tests for race_management module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from race_management import (
    create_race, assign_driver_to_race, assign_car_to_race, start_race,
    get_race, list_races
)
from registration import register_member
from inventory import add_car, update_car_condition


class TestCreateRace:
    """Test race creation."""

    def test_create_race_valid(self, reset_store):
        """Create race with valid parameters."""
        race = create_race("Night Run", "Downtown", 5000.0)
        assert race.name == "Night Run"
        assert race.location == "Downtown"
        assert race.prize_money == 5000.0
        assert race.status == "upcoming"
        assert race.driver_id == ""
        assert race.car_id == ""
        assert race.winner_id == ""

    def test_create_race_zero_prize_raises_error(self, reset_store):
        """Prize money of 0 should raise ValueError."""
        with pytest.raises(ValueError):
            create_race("Bad Race", "Nowhere", 0)

    def test_create_race_negative_prize_raises_error(self, reset_store):
        """Negative prize money should raise ValueError."""
        with pytest.raises(ValueError):
            create_race("Bad Race", "Nowhere", -1000.0)


class TestAssignDriverToRace:
    """Test driver assignment to races."""

    def test_assign_driver_valid_driver(self, reset_store, registered_driver):
        """Assign driver with role 'driver' should succeed."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        result = assign_driver_to_race(race.race_id, registered_driver.member_id)
        assert result.driver_id == registered_driver.member_id

    def test_assign_driver_mechanic_fails(self, reset_store, registered_mechanic):
        """Assign mechanic to race should raise ValueError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(ValueError) as exc_info:
            assign_driver_to_race(race.race_id, registered_mechanic.member_id)
        assert "driver" in str(exc_info.value).lower()

    def test_assign_driver_unavailable_fails(self, reset_store, registered_driver):
        """Assign unavailable driver should raise ValueError."""
        registered_driver.is_available = False
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(ValueError) as exc_info:
            assign_driver_to_race(race.race_id, registered_driver.member_id)
        assert "not available" in str(exc_info.value).lower()

    def test_assign_driver_nonexistent_fails(self, reset_store):
        """Assign non-existent driver should raise KeyError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(KeyError):
            assign_driver_to_race(race.race_id, "nonexistent-id")

    def test_assign_driver_sets_unavailable(self, reset_store, registered_driver):
        """After assignment, driver should be unavailable."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assert registered_driver.is_available is True
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        # Fetch the driver again from store to see updated state
        from registration import get_member
        driver = get_member(registered_driver.member_id)
        assert driver.is_available is False


class TestAssignCarToRace:
    """Test car assignment to races."""

    def test_assign_car_valid_car(self, reset_store, available_car):
        """Assign available car in good condition should succeed."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        result = assign_car_to_race(race.race_id, available_car.car_id)
        assert result.car_id == available_car.car_id

    def test_assign_car_unavailable_fails(self, reset_store, available_car):
        """Assign unavailable car should raise ValueError."""
        available_car.is_available = False
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(ValueError):
            assign_car_to_race(race.race_id, available_car.car_id)

    def test_assign_car_damaged_fails(self, reset_store, damaged_car):
        """Assign damaged car should raise ValueError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(ValueError) as exc_info:
            assign_car_to_race(race.race_id, damaged_car.car_id)
        assert "damaged" in str(exc_info.value).lower()

    def test_assign_car_nonexistent_fails(self, reset_store):
        """Assign non-existent car should raise KeyError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(KeyError):
            assign_car_to_race(race.race_id, "nonexistent-id")

    def test_assign_car_sets_unavailable(self, reset_store, available_car):
        """After assignment, car should be unavailable."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assert available_car.is_available is True
        assign_car_to_race(race.race_id, available_car.car_id)
        # Fetch car again from store
        from inventory import get_car
        car = get_car(available_car.car_id)
        assert car.is_available is False


class TestStartRace:
    """Test race start."""

    def test_start_race_without_driver_fails(self, reset_store, available_car):
        """Start race without driver should raise ValueError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_car_to_race(race.race_id, available_car.car_id)
        with pytest.raises(ValueError):
            start_race(race.race_id)

    def test_start_race_without_car_fails(self, reset_store, registered_driver):
        """Start race without car should raise ValueError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        with pytest.raises(ValueError):
            start_race(race.race_id)

    def test_start_race_with_both_succeeds(self, reset_store, registered_driver, available_car):
        """Start race with driver and car should succeed."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        result = start_race(race.race_id)
        assert result.status == "in_progress"


class TestGetRace:
    """Test race retrieval."""

    def test_get_race_valid_id(self, reset_store):
        """Retrieve race by valid ID."""
        created = create_race("Test Race", "Somewhere", 3000.0)
        retrieved = get_race(created.race_id)
        assert retrieved.race_id == created.race_id
        assert retrieved.name == "Test Race"

    def test_get_race_invalid_id_raises_keyerror(self, reset_store):
        """Retrieve with invalid ID should raise KeyError."""
        with pytest.raises(KeyError):
            get_race("nonexistent-id")


class TestListRaces:
    """Test race listing."""

    def test_list_races_empty(self, reset_store):
        """List races when none exist."""
        races = list_races()
        assert races == []

    def test_list_races_returns_all(self, reset_store):
        """List should return all races."""
        race1 = create_race("Race1", "Loc1", 1000.0)
        race2 = create_race("Race2", "Loc2", 2000.0)
        race3 = create_race("Race3", "Loc3", 3000.0)

        all_races = list_races()
        assert len(all_races) == 3

    def test_list_races_filter_by_status(self, reset_store, registered_driver, available_car):
        """Filter races by status."""
        race1 = create_race("Race1", "Loc1", 1000.0)
        race2 = create_race("Race2", "Loc2", 2000.0)

        assign_driver_to_race(race2.race_id, registered_driver.member_id)
        assign_car_to_race(race2.race_id, available_car.car_id)
        start_race(race2.race_id)

        upcoming = list_races("upcoming")
        assert len(upcoming) == 1
        assert upcoming[0].race_id == race1.race_id

        in_progress = list_races("in_progress")
        assert len(in_progress) == 1
        assert in_progress[0].race_id == race2.race_id
