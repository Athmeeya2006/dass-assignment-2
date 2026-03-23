"""Unit tests for leaderboard module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from leaderboard import get_full_leaderboard, get_top_driver, get_mission_success_rate
from registration import register_member
from race_management import create_race, assign_driver_to_race, assign_car_to_race, start_race
from results import record_result
from inventory import add_car
from mission_planning import create_mission, assign_mission, complete_mission, fail_mission


class TestGetFullLeaderboard:
    """Test full leaderboard retrieval."""

    def test_get_full_leaderboard_empty(self, reset_store):
        """Get leaderboard when no races completed."""
        leaderboard = get_full_leaderboard()
        assert leaderboard == []

    def test_get_full_leaderboard_single_entry(self, reset_store, registered_driver, available_car):
        """Get leaderboard with one completed race."""
        race = create_race("Test Race", "Somewhere", 5000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)
        record_result(race.race_id, registered_driver.member_id, "good")

        leaderboard = get_full_leaderboard()
        assert len(leaderboard) == 1
        entry = leaderboard[0]
        assert entry["member_id"] == registered_driver.member_id
        assert entry["name"] == "Ana Torrez"
        assert entry["wins"] == 1
        assert entry["earnings"] == 5000.0

    def test_get_full_leaderboard_multiple_entries_sorted(self, reset_store):
        """Get leaderboard with multiple drivers sorted correctly."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)

        # Driver1 wins 2 races
        race1 = create_race("Race1", "Loc1", 10000.0)
        assign_driver_to_race(race1.race_id, driver1.member_id)
        assign_car_to_race(race1.race_id, car1.car_id)
        start_race(race1.race_id)
        record_result(race1.race_id, driver1.member_id, "good")

        race2 = create_race("Race2", "Loc2", 20000.0)
        car1b = add_car("Car1b", 5)
        assign_driver_to_race(race2.race_id, driver1.member_id)
        assign_car_to_race(race2.race_id, car1b.car_id)
        start_race(race2.race_id)
        record_result(race2.race_id, driver1.member_id, "good")

        # Driver2 wins 1 race
        race3 = create_race("Race3", "Loc3", 5000.0)
        assign_driver_to_race(race3.race_id, driver2.member_id)
        assign_car_to_race(race3.race_id, car2.car_id)
        start_race(race3.race_id)
        record_result(race3.race_id, driver2.member_id, "good")

        leaderboard = get_full_leaderboard()
        assert len(leaderboard) == 2
        assert leaderboard[0]["member_id"] == driver1.member_id
        assert leaderboard[0]["name"] == "Driver1"
        assert leaderboard[0]["wins"] == 2


class TestGetTopDriver:
    """Test top driver retrieval."""

    def test_get_top_driver_empty(self, reset_store):
        """Get top drivers when leaderboard empty."""
        top = get_top_driver(3)
        assert top == []

    def test_get_top_driver_three_drivers(self, reset_store):
        """Get top N drivers with multiple drivers on leaderboard."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        driver3 = register_member("Driver3", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)
        car3 = add_car("Car3", 7)

        # Each driver wins one race
        for i, driver in enumerate([driver1, driver2, driver3], 1):
            car = [car1, car2, car3][i-1]
            race = create_race(f"Race{i}", f"Loc{i}", float(i * 1000))
            assign_driver_to_race(race.race_id, driver.member_id)
            assign_car_to_race(race.race_id, car.car_id)
            start_race(race.race_id)
            record_result(race.race_id, driver.member_id, "good")

        top3 = get_top_driver(3)
        assert len(top3) == 3

        top1 = get_top_driver(1)
        assert len(top1) == 1
        assert top1[0]["member_id"] == driver3.member_id

        top2 = get_top_driver(2)
        assert len(top2) == 2


class TestGetMissionSuccessRate:
    """Test mission success rate calculation."""

    def test_get_mission_success_rate_no_missions(self, reset_store):
        """Success rate with no missions."""
        stats = get_mission_success_rate()
        assert stats["total"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate_percent"] == 0.0

    def test_get_mission_success_rate_all_completed(self, reset_store, registered_driver):
        """Success rate with all missions completed."""
        # Create and complete one mission
        m1 = create_mission("M1", "delivery", ["driver"])
        assign_mission(m1.mission_id)
        complete_mission(m1.mission_id)

        stats = get_mission_success_rate()
        assert stats["total"] == 1
        assert stats["completed"] == 1
        assert stats["failed"] == 0
        assert stats["success_rate_percent"] == 100.0

    def test_get_mission_success_rate_mixed(self, reset_store):
        """Success rate with completed and failed missions."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")

        # Complete one mission
        m1 = create_mission("M1", "delivery", ["driver"])
        assign_mission(m1.mission_id)
        complete_mission(m1.mission_id)

        # Fail another mission
        m2 = create_mission("M2", "delivery", ["driver"])
        assign_mission(m2.mission_id)
        fail_mission(m2.mission_id, "error")

        stats = get_mission_success_rate()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["success_rate_percent"] == 50.0

    def test_get_mission_success_rate_all_failed(self, reset_store):
        """Success rate with all missions failed."""
        driver = register_member("Driver", "driver")

        m1 = create_mission("M1", "delivery", ["driver"])
        assign_mission(m1.mission_id)
        fail_mission(m1.mission_id, "error")

        m2 = create_mission("M2", "delivery", ["driver"])
        assign_mission(m2.mission_id)
        fail_mission(m2.mission_id, "error")

        stats = get_mission_success_rate()
        assert stats["total"] == 2
        assert stats["completed"] == 0
        assert stats["failed"] == 2
        assert stats["success_rate_percent"] == 0.0
