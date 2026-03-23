"""Unit tests for garage module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from garage import repair_car, get_repair_log, get_cars_needing_repair
from inventory import add_car, update_car_condition
from registration import register_member


class TestRepairCar:
    """Test car repair."""

    def test_repair_car_valid_mechanic(self, reset_store, registered_mechanic, damaged_car):
        """Repair damaged car with available mechanic."""
        repaired = repair_car(damaged_car.car_id, registered_mechanic.member_id)
        assert repaired.condition == "good"

    def test_repair_car_non_mechanic_fails(self, reset_store, registered_driver, damaged_car):
        """Repair with non-mechanic should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            repair_car(damaged_car.car_id, registered_driver.member_id)
        assert "mechanic" in str(exc_info.value).lower()

    def test_repair_car_unavailable_mechanic_fails(self, reset_store, registered_mechanic, damaged_car):
        """Repair with unavailable mechanic should raise ValueError."""
        registered_mechanic.is_available = False
        with pytest.raises(ValueError) as exc_info:
            repair_car(damaged_car.car_id, registered_mechanic.member_id)
        assert "not available" in str(exc_info.value).lower()

    def test_repair_car_non_damaged_fails(self, reset_store, registered_mechanic, available_car):
        """Repair non-damaged car should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            repair_car(available_car.car_id, registered_mechanic.member_id)
        assert "does not need repair" in str(exc_info.value).lower()

    def test_repair_car_nonexistent_car_fails(self, reset_store, registered_mechanic):
        """Repair non-existent car should raise KeyError."""
        with pytest.raises(KeyError):
            repair_car("nonexistent-id", registered_mechanic.member_id)

    def test_repair_car_nonexistent_mechanic_fails(self, reset_store, damaged_car):
        """Repair with non-existent mechanic should raise KeyError."""
        with pytest.raises(KeyError):
            repair_car(damaged_car.car_id, "nonexistent-id")

    def test_repair_car_adds_to_log(self, reset_store, registered_mechanic, damaged_car):
        """Repair should add entry to repair log."""
        repair_log = get_repair_log()
        assert len(repair_log) == 0

        repair_car(damaged_car.car_id, registered_mechanic.member_id)
        repair_log = get_repair_log()
        assert len(repair_log) == 1
        entry = repair_log[0]
        assert entry["car_id"] == damaged_car.car_id
        assert entry["mechanic_id"] == registered_mechanic.member_id
        assert "timestamp" in entry


class TestGetRepairLog:
    """Test repair log retrieval."""

    def test_get_repair_log_empty(self, reset_store):
        """Get repair log when no repairs."""
        log = get_repair_log()
        assert log == []

    def test_get_repair_log_multiple_repairs(self, reset_store, registered_mechanic):
        """Get repair log with multiple repairs."""
        car1 = add_car("Car1", 5)
        car1 = update_car_condition(car1.car_id, "damaged")
        car2 = add_car("Car2", 6)
        car2 = update_car_condition(car2.car_id, "damaged")

        repair_car(car1.car_id, registered_mechanic.member_id)
        repair_car(car2.car_id, registered_mechanic.member_id)

        log = get_repair_log()
        assert len(log) == 2


class TestGetCarsNeedingRepair:
    """Test finding cars that need repair."""

    def test_get_cars_needing_repair_empty(self, reset_store):
        """Get cars needing repair when all are good."""
        cars = get_cars_needing_repair()
        assert cars == []

    def test_get_cars_needing_repair_returns_damaged_only(self, reset_store):
        """Get cars needing repair returns only damaged cars."""
        car1 = add_car("Good Car", 5)
        car2 = add_car("Damaged Car", 6)
        car2 = update_car_condition(car2.car_id, "damaged")
        car3 = add_car("Also Good", 7)

        needing_repair = get_cars_needing_repair()
        assert len(needing_repair) == 1
        assert needing_repair[0].car_id == car2.car_id
        assert needing_repair[0].condition == "damaged"

    def test_get_cars_needing_repair_multiple_damaged(self, reset_store):
        """Get cars needing repair with multiple damaged cars."""
        car1 = add_car("Damaged1", 5)
        car1 = update_car_condition(car1.car_id, "damaged")
        car2 = add_car("Good", 6)
        car3 = add_car("Damaged2", 7)
        car3 = update_car_condition(car3.car_id, "damaged")

        needing_repair = get_cars_needing_repair()
        assert len(needing_repair) == 2
        ids = [car.car_id for car in needing_repair]
        assert car1.car_id in ids
        assert car3.car_id in ids
