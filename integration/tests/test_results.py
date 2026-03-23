"""Unit tests for results module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from results import record_result, get_rankings, get_driver_stats
from race_management import (
    create_race, assign_driver_to_race, assign_car_to_race, start_race
)
from registration import register_member, get_member
from inventory import add_car, get_cash_balance, add_cash


class TestRecordResult:
    """Test race result recording."""

    def test_record_result_valid_in_progress_race(self, reset_store, ready_race, registered_driver, available_car):
        """Record result for in-progress race should succeed."""
        initial_balance = get_cash_balance()
        race = record_result(ready_race.race_id, registered_driver.member_id, "good")

        assert race.status == "completed"
        assert race.winner_id == registered_driver.member_id
        assert get_cash_balance() == initial_balance + ready_race.prize_money

    def test_record_result_upcoming_race_fails(self, reset_store, registered_driver):
        """Record result on upcoming race should raise ValueError."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        with pytest.raises(ValueError) as exc_info:
            record_result(race.race_id, registered_driver.member_id, "good")
        assert "in progress" in str(exc_info.value).lower()

    def test_record_result_wrong_winner_fails(self, reset_store, ready_race, registered_driver):
        """Record result with different winner than assigned driver should raise ValueError."""
        other_driver = register_member("Other Driver", "driver")
        with pytest.raises(ValueError) as exc_info:
            record_result(ready_race.race_id, other_driver.member_id, "good")
        assert "winner" in str(exc_info.value).lower() or "driver" in str(exc_info.value).lower()

    def test_record_result_updates_cash_balance(self, reset_store, registered_driver, available_car):
        """Record result should add prize money to cash balance."""
        race = create_race("Test Race", "Somewhere", 5000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)

        initial_balance = get_cash_balance()
        record_result(race.race_id, registered_driver.member_id, "good")
        assert get_cash_balance() == initial_balance + 5000.0

    def test_record_result_updates_car_condition(self, reset_store, registered_driver, available_car):
        """Record result should update car condition."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)

        from inventory import get_car
        record_result(race.race_id, registered_driver.member_id, "damaged")
        car = get_car(available_car.car_id)
        assert car.condition == "damaged"

    def test_record_result_frees_driver(self, reset_store, registered_driver, available_car):
        """Record result should mark driver as available again."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)

        assert get_member(registered_driver.member_id).is_available is False
        record_result(race.race_id, registered_driver.member_id, "good")
        assert get_member(registered_driver.member_id).is_available is True

    def test_record_result_frees_car(self, reset_store, registered_driver, available_car):
        """Record result should mark car as available again."""
        race = create_race("Test Race", "Somewhere", 3000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)

        from inventory import get_car
        assert get_car(available_car.car_id).is_available is False
        record_result(race.race_id, registered_driver.member_id, "good")
        assert get_car(available_car.car_id).is_available is True


class TestGetRankings:
    """Test driver rankings."""

    def test_get_rankings_empty(self, reset_store):
        """Get rankings when no races completed."""
        rankings = get_rankings()
        assert rankings == []

    def test_get_rankings_single_winner(self, reset_store, registered_driver, available_car):
        """Get rankings with one race completed."""
        race = create_race("Test Race", "Somewhere", 5000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)
        record_result(race.race_id, registered_driver.member_id, "good")

        rankings = get_rankings()
        assert len(rankings) == 1
        assert rankings[0]["member_id"] == registered_driver.member_id
        assert rankings[0]["wins"] == 1
        assert rankings[0]["earnings"] == 5000.0

    def test_get_rankings_sorted_by_wins(self, reset_store):
        """Rankings should be sorted by wins descending."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)

        # Driver1 wins 2 races
        race1 = create_race("Race1", "Loc1", 1000.0)
        assign_driver_to_race(race1.race_id, driver1.member_id)
        assign_car_to_race(race1.race_id, car1.car_id)
        start_race(race1.race_id)
        record_result(race1.race_id, driver1.member_id, "good")

        race2 = create_race("Race2", "Loc2", 2000.0)
        car1_new = add_car("Car1b", 5)
        assign_driver_to_race(race2.race_id, driver1.member_id)
        assign_car_to_race(race2.race_id, car1_new.car_id)
        start_race(race2.race_id)
        record_result(race2.race_id, driver1.member_id, "good")

        # Driver2 wins 1 race
        race3 = create_race("Race3", "Loc3", 1000.0)
        assign_driver_to_race(race3.race_id, driver2.member_id)
        assign_car_to_race(race3.race_id, car2.car_id)
        start_race(race3.race_id)
        record_result(race3.race_id, driver2.member_id, "good")

        rankings = get_rankings()
        assert rankings[0]["member_id"] == driver1.member_id
        assert rankings[0]["wins"] == 2
        assert rankings[1]["member_id"] == driver2.member_id
        assert rankings[1]["wins"] == 1

    def test_get_rankings_sorted_by_earnings_secondary(self, reset_store):
        """Rankings with same wins sorted by earnings."""
        driver1 = register_member("Driver1", "driver")
        driver2 = register_member("Driver2", "driver")
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 6)

        # Both drivers win 1 race
        race1 = create_race("Race1", "Loc1", 10000.0)
        assign_driver_to_race(race1.race_id, driver1.member_id)
        assign_car_to_race(race1.race_id, car1.car_id)
        start_race(race1.race_id)
        record_result(race1.race_id, driver1.member_id, "good")

        race2 = create_race("Race2", "Loc2", 5000.0)
        assign_driver_to_race(race2.race_id, driver2.member_id)
        assign_car_to_race(race2.race_id, car2.car_id)
        start_race(race2.race_id)
        record_result(race2.race_id, driver2.member_id, "good")

        rankings = get_rankings()
        assert rankings[0]["member_id"] == driver1.member_id
        assert rankings[0]["earnings"] == 10000.0


class TestGetDriverStats:
    """Test individual driver stats."""

    def test_get_driver_stats_after_race(self, reset_store, registered_driver, available_car):
        """Get stats for driver after winning race."""
        race = create_race("Test Race", "Somewhere", 5000.0)
        assign_driver_to_race(race.race_id, registered_driver.member_id)
        assign_car_to_race(race.race_id, available_car.car_id)
        start_race(race.race_id)
        record_result(race.race_id, registered_driver.member_id, "good")

        stats = get_driver_stats(registered_driver.member_id)
        assert stats["member_id"] == registered_driver.member_id
        assert stats["name"] == "Ana Torrez"
        assert stats["wins"] == 1
        assert stats["earnings"] == 5000.0

    def test_get_driver_stats_nonexistent_driver_fails(self, reset_store):
        """Get stats for driver with no races should raise KeyError."""
        with pytest.raises(KeyError):
            get_driver_stats("nonexistent-id")
