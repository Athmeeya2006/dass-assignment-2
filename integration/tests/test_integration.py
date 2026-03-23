"""Integration tests for StreetRace Manager system."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from registration import register_member, get_member
from crew_management import assign_role, set_availability, get_available_by_role, update_skill_level
from inventory import add_car, update_car_condition, get_cash_balance, add_cash
from race_management import (
    create_race, assign_driver_to_race, assign_car_to_race, start_race
)
from results import record_result, get_rankings, get_driver_stats
from mission_planning import (
    create_mission, assign_mission, complete_mission, fail_mission
)
from leaderboard import get_full_leaderboard, get_top_driver
from garage import repair_car


class TestIntegrationScenarios:
    """Integration scenarios combining multiple modules."""

    def test_scenario_1_full_race_pipeline_updates_cash(self, reset_store):
        """
        Scenario 1: Register driver, add car, create race, assign both, 
                   start race, record result. Verify prize money is added.
        Modules: registration → race_management → results → inventory
        """
        # Register driver
        driver = register_member("Ana Torrez", "driver")
        
        # Add car
        car = add_car("Nitro X", 8)
        
        # Create race with prize
        race = create_race("Night Run", "Downtown", 5000.0)
        
        # Assign driver and car
        assign_driver_to_race(race.race_id, driver.member_id)
        assign_car_to_race(race.race_id, car.car_id)
        
        # Start race
        race = start_race(race.race_id)
        assert race.status == "in_progress"
        
        # Record result
        initial_balance = get_cash_balance()
        race = record_result(race.race_id, driver.member_id, "good")
        
        # Verify
        assert race.status == "completed"
        assert race.winner_id == driver.member_id
        assert get_cash_balance() == initial_balance + 5000.0

    def test_scenario_2_non_driver_cannot_enter_race(self, reset_store):
        """
        Scenario 2: Non-driver (mechanic) tries to enter a race
        Modules: registration → race_management
        Expected: ValueError raised
        """
        mechanic = register_member("Bob Wrench", "mechanic")
        car = add_car("Test Car", 5)
        race = create_race("Test Race", "Somewhere", 1000.0)
        
        assign_car_to_race(race.race_id, car.car_id)
        
        with pytest.raises(ValueError) as exc_info:
            assign_driver_to_race(race.race_id, mechanic.member_id)
        assert "driver" in str(exc_info.value).lower()

    def test_scenario_3_unregistered_member_cannot_enter_race(self, reset_store):
        """
        Scenario 3: Unregistered member cannot be assigned to race
        Modules: race_management → registration (lookup fails)
        Expected: KeyError because member doesn't exist
        """
        race = create_race("Test Race", "Somewhere", 1000.0)
        
        with pytest.raises(KeyError):
            assign_driver_to_race(race.race_id, "ghost-99")

    def test_scenario_4_damaged_car_cannot_be_assigned_to_race(self, reset_store):
        """
        Scenario 4: Damaged car cannot be assigned to race
        Modules: race_management → inventory
        Expected: ValueError raised
        """
        driver = register_member("Ana", "driver")
        car = add_car("Test Car", 5)
        update_car_condition(car.car_id, "damaged")
        race = create_race("Test Race", "Somewhere", 1000.0)
        
        assign_driver_to_race(race.race_id, driver.member_id)
        
        with pytest.raises(ValueError) as exc_info:
            assign_car_to_race(race.race_id, car.car_id)
        assert "damaged" in str(exc_info.value).lower()

    def test_scenario_5_mission_fails_when_no_available_driver(self, reset_store):
        """
        Scenario 5: Mission fails when required role (driver) unavailable
        Modules: mission_planning → crew_management
        Expected: ValueError raised mentioning the missing role
        """
        mission = create_mission("Test Mission", "delivery", ["driver"])
        
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "driver" in str(exc_info.value).lower()

    def test_scenario_6_mission_with_damaged_car_requires_mechanic(self, reset_store):
        """
        Scenario 6: Mission with damaged car requires available mechanic
        Modules: mission_planning → crew_management
        """
        driver = register_member("Driver", "driver")
        mission = create_mission("Test Mission", "delivery", ["driver"], 
                                involves_damaged_car=True)
        
        # No mechanic registered
        with pytest.raises(ValueError) as exc_info:
            assign_mission(mission.mission_id)
        assert "mechanic" in str(exc_info.value).lower()

    def test_scenario_7_mission_succeeds_with_all_roles_available(self, reset_store):
        """
        Scenario 7: Mission succeeds when all required roles are available
        Modules: registration → crew_management → mission_planning
        """
        driver = register_member("Driver", "driver")
        mechanic = register_member("Mechanic", "mechanic")
        
        mission = create_mission("Test Mission", "delivery", ["driver", "mechanic"])
        
        # Before assignment
        assert driver.is_available is True
        assert mechanic.is_available is True
        
        # Assign mission
        assigned = assign_mission(mission.mission_id)
        assert assigned.status == "active"
        assert driver.member_id in assigned.assigned_members
        assert mechanic.member_id in assigned.assigned_members
        
        # After assignment, both unavailable
        driver_after = get_member(driver.member_id)
        mechanic_after = get_member(mechanic.member_id)
        assert driver_after.is_available is False
        assert mechanic_after.is_available is False
        
        # Complete mission
        completed = complete_mission(assigned.mission_id)
        assert completed.status == "completed"
        
        # After completion, both available again
        driver_final = get_member(driver.member_id)
        mechanic_final = get_member(mechanic.member_id)
        assert driver_final.is_available is True
        assert mechanic_final.is_available is True

    def test_scenario_8_driver_available_after_race_completion(self, reset_store, ready_race, registered_driver):
        """
        Scenario 8: Driver availability released after race completes
        Modules: results → crew_management
        Driver should be unavailable during race, available after.
        """
        # Before recording result
        driver_before = get_member(registered_driver.member_id)
        assert driver_before.is_available is False
        
        # Record result
        record_result(ready_race.race_id, registered_driver.member_id, "good")
        
        # After recording result
        driver_after = get_member(registered_driver.member_id)
        assert driver_after.is_available is True

    def test_scenario_9_leaderboard_reflects_race_outcomes(self, reset_store):
        """
        Scenario 9: Leaderboard reflects race outcomes correctly
        Modules: registration → race_management → results → leaderboard
        """
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)
        
        # Race 1: driver1 wins with 2000 prize
        race1 = create_race("Race1", "Loc1", 2000.0)
        assign_driver_to_race(race1.race_id, driver1.member_id)
        assign_car_to_race(race1.race_id, car1.car_id)
        start_race(race1.race_id)
        record_result(race1.race_id, driver1.member_id, "good")
        
        # Race 2: driver2 wins with 5000 prize (more earnings despite same wins)
        race2 = create_race("Race2", "Loc2", 5000.0)
        assign_driver_to_race(race2.race_id, driver2.member_id)
        assign_car_to_race(race2.race_id, car2.car_id)
        start_race(race2.race_id)
        record_result(race2.race_id, driver2.member_id, "good")
        
        # Get leaderboard
        leaderboard = get_full_leaderboard()
        assert len(leaderboard) == 2
        assert leaderboard[0]["member_id"] == driver2.member_id  # Sorted by earnings
        assert leaderboard[0]["earnings"] == 5000.0
        assert leaderboard[1]["member_id"] == driver1.member_id
        assert leaderboard[1]["earnings"] == 2000.0

    def test_scenario_10_repaired_car_can_be_assigned_to_race(self, reset_store):
        """
        Scenario 10: Garage repair enables damaged car to be used in race
        Modules: inventory → garage → race_management
        A damaged car cannot enter a race. After repair it can.
        """
        driver = register_member("Driver", "driver")
        car = add_car("Car", 5)
        update_car_condition(car.car_id, "damaged")
        mechanic = register_member("Mechanic", "mechanic")
        
        # Try to use damaged car - should fail
        race = create_race("Race1", "Loc1", 3000.0)
        assign_driver_to_race(race.race_id, driver.member_id)
        try:
            assign_car_to_race(race.race_id, car.car_id)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        # Repair the car
        repaired_car = repair_car(car.car_id, mechanic.member_id)
        assert repaired_car.condition == "good"
        
        # Now assign car to race should succeed
        race2 = create_race("Race2", "Loc2", 3000.0)
        driver2 = register_member("Driver2", "driver")
        assign_driver_to_race(race2.race_id, driver2.member_id)
        result = assign_car_to_race(race2.race_id, car.car_id)
        assert result.car_id == car.car_id

    def test_scenario_11_role_change_enables_race_entry(self, reset_store):
        """
        Scenario 11: Role update allows member to enter races
        Modules: registration → crew_management → race_management
        A strategist can't enter a race. After role change to driver, they can.
        """
        strategist = register_member("Strategist", "strategist")
        car = add_car("Car", 5)
        
        # Try to assign strategist to race - should fail
        race = create_race("Race1", "Loc1", 3000.0)
        assign_car_to_race(race.race_id, car.car_id)
        try:
            assign_driver_to_race(race.race_id, strategist.member_id)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        # Change role to driver
        updated = assign_role(strategist.member_id, "driver")
        assert updated.role == "driver"
        
        # Now assign to race should succeed
        race2 = create_race("Race2", "Loc2", 3000.0)
        car2 = add_car("Car2", 6)
        assign_car_to_race(race2.race_id, car2.car_id)
        result = assign_driver_to_race(race2.race_id, strategist.member_id)
        assert result.driver_id == strategist.member_id

    def test_scenario_12_complete_mission_frees_all_assigned_crew(self, reset_store):
        """
        Scenario 12: Complete mission frees all assigned crew members
        Modules: mission_planning → crew_management
        All crew assigned to a mission must be freed when it completes.
        """
        driver = register_member("Driver", "driver")
        mechanic = register_member("Mechanic", "mechanic")
        strategist = register_member("Strategist", "strategist")
        
        mission = create_mission("Complex Mission", "rescue", 
                                ["driver", "mechanic", "strategist"])
        
        # Assign mission - all three become unavailable
        assigned = assign_mission(mission.mission_id)
        assert driver.member_id in assigned.assigned_members
        assert mechanic.member_id in assigned.assigned_members
        assert strategist.member_id in assigned.assigned_members
        
        driver_assigned = get_member(driver.member_id)
        mechanic_assigned = get_member(mechanic.member_id)
        strategist_assigned = get_member(strategist.member_id)
        assert driver_assigned.is_available is False
        assert mechanic_assigned.is_available is False
        assert strategist_assigned.is_available is False
        
        # Complete mission - all three become available
        completed = complete_mission(assigned.mission_id)
        
        driver_freed = get_member(driver.member_id)
        mechanic_freed = get_member(mechanic.member_id)
        strategist_freed = get_member(strategist.member_id)
        assert driver_freed.is_available is True
        assert mechanic_freed.is_available is True
        assert strategist_freed.is_available is True


class TestCrossModuleInteractions:
    """Test complex interactions across modules."""

    def test_sequential_races_with_multiple_drivers(self, reset_store):
        """Driver becomes available after race completion, can participate in next race."""
        driver = register_member("Ana", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)
        
        # First race
        race1 = create_race("Race1", "Loc1", 1000.0)
        assign_driver_to_race(race1.race_id, driver.member_id)
        assign_car_to_race(race1.race_id, car1.car_id)
        start_race(race1.race_id)
        
        # Driver should be unavailable
        assert get_member(driver.member_id).is_available is False
        
        record_result(race1.race_id, driver.member_id, "good")
        
        # Driver should be available for second race
        assert get_member(driver.member_id).is_available is True
        
        race2 = create_race("Race2", "Loc2", 2000.0)
        assign_driver_to_race(race2.race_id, driver.member_id)
        assign_car_to_race(race2.race_id, car2.car_id)
        start_race(race2.race_id)
        record_result(race2.race_id, driver.member_id, "good")
        
        # Check rankings
        stats = get_driver_stats(driver.member_id)
        assert stats["wins"] == 2
        assert stats["earnings"] == 3000.0

    def test_mission_concurrent_with_races(self, reset_store):
        """A driver in a mission cannot participate in a race."""
        driver = register_member("Ana", "driver")
        car = add_car("Car", 5)
        
        # Create and assign mission (driver becomes unavailable)
        mission = create_mission("Delivery", "delivery", ["driver"])
        assign_mission(mission.mission_id)
        
        # Verify driver is unavailable
        assert get_member(driver.member_id).is_available is False
        
        # Try to assign same driver to race - should fail
        race = create_race("Race", "Loc", 1000.0)
        assign_car_to_race(race.race_id, car.car_id)
        with pytest.raises(ValueError) as exc_info:
            assign_driver_to_race(race.race_id, driver.member_id)
        assert "not available" in str(exc_info.value).lower()
