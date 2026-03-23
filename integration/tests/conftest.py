import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from store import store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset all state before and after every test."""
    store.reset()
    yield
    store.reset()


@pytest.fixture
def registered_driver():
    from registration import register_member
    return register_member("Ana Torrez", "driver")


@pytest.fixture
def registered_mechanic():
    from registration import register_member
    return register_member("Bob Wrench", "mechanic")


@pytest.fixture
def registered_strategist():
    from registration import register_member
    return register_member("Cam Stone", "strategist")


@pytest.fixture
def registered_navigator():
    from registration import register_member
    return register_member("Dan Rivers", "navigator")


@pytest.fixture
def available_car():
    from inventory import add_car
    return add_car("Nitro X", speed_rating=8)


@pytest.fixture
def damaged_car():
    from inventory import add_car, update_car_condition
    car = add_car("Rusty Bolt", speed_rating=4)
    return update_car_condition(car.car_id, "damaged")


@pytest.fixture
def basic_race():
    from race_management import create_race
    return create_race("Night Run", "Downtown", 5000.0)


@pytest.fixture
def ready_race(registered_driver, available_car):
    """Race with driver and car assigned, status in_progress."""
    from race_management import (create_race, assign_driver_to_race,
                                  assign_car_to_race, start_race)
    race = create_race("Sprint", "Uptown", 3000.0)
    assign_driver_to_race(race.race_id, registered_driver.member_id)
    assign_car_to_race(race.race_id, available_car.car_id)
    return start_race(race.race_id)
