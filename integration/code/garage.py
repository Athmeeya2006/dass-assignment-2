from datetime import datetime

from inventory import get_car, update_car_condition
from registration import get_member
from models import Car
from store import store


def repair_car(car_id: str, mechanic_id: str) -> Car:
    car = get_car(car_id)
    mechanic = get_member(mechanic_id)

    if mechanic.role != "mechanic":
        raise ValueError("Only mechanics can repair cars")
    if not mechanic.is_available:
        raise ValueError("Mechanic is not available")
    if car.condition != "damaged":
        raise ValueError("Car does not need repair")

    update_car_condition(car_id, "good")

    store.repair_log.append(
        {
            "car_id": car_id,
            "mechanic_id": mechanic_id,
            "timestamp": datetime.now().isoformat(),
        }
    )
    return store.cars[car_id]


def get_repair_log() -> list[dict]:
    return store.repair_log


def get_cars_needing_repair() -> list[Car]:
    return [car for car in store.cars.values() if car.condition == "damaged"]
