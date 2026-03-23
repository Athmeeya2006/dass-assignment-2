"""Unit tests for inventory module."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from inventory import (
    add_car, get_car, list_cars, update_car_condition,
    add_inventory_item, get_cash_balance, add_cash, deduct_cash
)


class TestAddCar:
    """Test car addition."""

    def test_add_car_valid(self, reset_store):
        """Add car with valid parameters."""
        car = add_car("Nitro X", 8)
        assert car.name == "Nitro X"
        assert car.speed_rating == 8
        assert car.condition == "excellent"
        assert car.is_available is True

    def test_add_car_speed_rating_boundary_1(self, reset_store):
        """Add car with speed rating 1 (minimum boundary)."""
        car = add_car("Slow", 1)
        assert car.speed_rating == 1

    def test_add_car_speed_rating_boundary_10(self, reset_store):
        """Add car with speed rating 10 (maximum boundary)."""
        car = add_car("Fast", 10)
        assert car.speed_rating == 10

    def test_add_car_speed_rating_zero_raises_error(self, reset_store):
        """Speed rating 0 should raise ValueError."""
        with pytest.raises(ValueError):
            add_car("Bad", 0)

    def test_add_car_speed_rating_11_raises_error(self, reset_store):
        """Speed rating 11 should raise ValueError."""
        with pytest.raises(ValueError):
            add_car("Bad", 11)


class TestGetCar:
    """Test car retrieval."""

    def test_get_car_valid_id(self, reset_store):
        """Retrieve car by valid ID."""
        added = add_car("Nitro X", 8)
        retrieved = get_car(added.car_id)
        assert retrieved.car_id == added.car_id
        assert retrieved.name == "Nitro X"

    def test_get_car_invalid_id_raises_keyerror(self, reset_store):
        """Retrieve with invalid ID should raise KeyError."""
        with pytest.raises(KeyError):
            get_car("nonexistent-id")


class TestListCars:
    """Test car listing."""

    def test_list_cars_empty(self, reset_store):
        """List cars when none added."""
        cars = list_cars()
        assert cars == []

    def test_list_cars_returns_all(self, reset_store):
        """List should return all cars."""
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 7)
        car3 = add_car("Car3", 9)

        all_cars = list_cars()
        assert len(all_cars) == 3

    def test_list_cars_available_only_filter(self, reset_store):
        """List available_only should exclude unavailable cars."""
        car1 = add_car("Car1", 5)
        car2 = add_car("Car2", 7)
        car1.is_available = False

        available = list_cars(available_only=True)
        assert len(available) == 1
        assert available[0].car_id == car2.car_id


class TestUpdateCarCondition:
    """Test car condition updates."""

    def test_update_car_condition_excellent(self, reset_store):
        """Update car condition to excellent."""
        car = add_car("Test", 5)
        updated = update_car_condition(car.car_id, "excellent")
        assert updated.condition == "excellent"

    def test_update_car_condition_good(self, reset_store):
        """Update car condition to good."""
        car = add_car("Test", 5)
        updated = update_car_condition(car.car_id, "good")
        assert updated.condition == "good"

    def test_update_car_condition_damaged(self, reset_store):
        """Update car condition to damaged."""
        car = add_car("Test", 5)
        updated = update_car_condition(car.car_id, "damaged")
        assert updated.condition == "damaged"

    def test_update_car_condition_invalid_raises_error(self, reset_store):
        """Invalid condition should raise ValueError."""
        car = add_car("Test", 5)
        with pytest.raises(ValueError):
            update_car_condition(car.car_id, "broken")

    def test_update_car_condition_nonexistent_car(self, reset_store):
        """Update condition on non-existent car should raise KeyError."""
        with pytest.raises(KeyError):
            update_car_condition("nonexistent-id", "good")


class TestAddInventoryItem:
    """Test inventory item addition."""

    def test_add_inventory_item_part_valid(self, reset_store):
        """Add inventory part with valid parameters."""
        item = add_inventory_item("part", "Brake Pads", 10)
        assert item.item_type == "part"
        assert item.name == "Brake Pads"
        assert item.quantity == 10

    def test_add_inventory_item_tool_valid(self, reset_store):
        """Add inventory tool with valid parameters."""
        item = add_inventory_item("tool", "Wrench", 5)
        assert item.item_type == "tool"
        assert item.quantity == 5

    def test_add_inventory_item_invalid_type(self, reset_store):
        """Invalid item type should raise ValueError."""
        with pytest.raises(ValueError):
            add_inventory_item("weapon", "Gun", 1)

    def test_add_inventory_item_zero_quantity_raises_error(self, reset_store):
        """Zero quantity should raise ValueError."""
        with pytest.raises(ValueError):
            add_inventory_item("part", "Bad", 0)

    def test_add_inventory_item_negative_quantity_raises_error(self, reset_store):
        """Negative quantity should raise ValueError."""
        with pytest.raises(ValueError):
            add_inventory_item("part", "Bad", -5)


class TestCashBalance:
    """Test cash management."""

    def test_get_cash_balance_initial(self, reset_store):
        """Initial cash balance should be 10000."""
        balance = get_cash_balance()
        assert balance == 10000.0

    def test_add_cash_positive_amount(self, reset_store):
        """Add positive cash amount."""
        new_balance = add_cash(1000.0)
        assert new_balance == 11000.0
        assert get_cash_balance() == 11000.0

    def test_add_cash_zero_raises_error(self, reset_store):
        """Add zero cash should raise ValueError."""
        with pytest.raises(ValueError):
            add_cash(0)

    def test_add_cash_negative_raises_error(self, reset_store):
        """Add negative cash should raise ValueError."""
        with pytest.raises(ValueError):
            add_cash(-100)

    def test_deduct_cash_valid_amount(self, reset_store):
        """Deduct valid cash amount."""
        new_balance = deduct_cash(1000.0)
        assert new_balance == 9000.0
        assert get_cash_balance() == 9000.0

    def test_deduct_cash_entire_balance(self, reset_store):
        """Deduct entire cash balance."""
        new_balance = deduct_cash(10000.0)
        assert new_balance == 0.0

    def test_deduct_cash_more_than_balance_raises_error(self, reset_store):
        """Deduct more than available should raise ValueError."""
        with pytest.raises(ValueError):
            deduct_cash(10001.0)

    def test_deduct_cash_zero_raises_error(self, reset_store):
        """Deduct zero should raise ValueError."""
        with pytest.raises(ValueError):
            deduct_cash(0)

    def test_deduct_cash_negative_raises_error(self, reset_store):
        """Deduct negative should raise ValueError."""
        with pytest.raises(ValueError):
            deduct_cash(-100)

    def test_add_and_deduct_sequence(self, reset_store):
        """Sequence of add and deduct operations."""
        add_cash(5000.0)
        assert get_cash_balance() == 15000.0
        deduct_cash(3000.0)
        assert get_cash_balance() == 12000.0
        add_cash(1000.0)
        assert get_cash_balance() == 13000.0
