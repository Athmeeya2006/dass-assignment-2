import uuid

from models import Car, InventoryItem
from store import store


VALID_CONDITIONS = ["excellent", "good", "damaged"]


def _new_car_id() -> str:
    return uuid.uuid4().hex[:8]


def _new_item_id() -> str:
    return uuid.uuid4().hex[:8]


def add_car(name: str, speed_rating: int) -> Car:
    if not 1 <= speed_rating <= 10:
        raise ValueError("speed_rating must be between 1 and 10")

    car = Car(
        car_id=_new_car_id(),
        name=name,
        speed_rating=speed_rating,
        condition="excellent",
        is_available=True,
    )
    store.cars[car.car_id] = car
    return car


def get_car(car_id: str) -> Car:
    return store.cars[car_id]


def list_cars(available_only: bool = False) -> list[Car]:
    cars = list(store.cars.values())
    if available_only:
        return [car for car in cars if car.is_available]
    return cars


def update_car_condition(car_id: str, condition: str) -> Car:
    if condition not in VALID_CONDITIONS:
        raise ValueError("Invalid condition")
    car = get_car(car_id)
    car.condition = condition
    return car


def add_inventory_item(item_type: str, name: str, quantity: int) -> InventoryItem:
    if item_type not in ("part", "tool"):
        raise ValueError("Invalid item type")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    item = InventoryItem(
        item_id=_new_item_id(),
        item_type=item_type,
        name=name,
        quantity=quantity,
    )
    store.inventory_items[item.item_id] = item
    return item


def get_cash_balance() -> float:
    return store.cash_balance


def add_cash(amount: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    store.cash_balance += amount
    return store.cash_balance


def deduct_cash(amount: float) -> float:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if amount > store.cash_balance:
        raise ValueError("Insufficient balance")
    store.cash_balance -= amount
    return store.cash_balance
