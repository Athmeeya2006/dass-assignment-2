import uuid

from crew_management import set_availability
from inventory import get_car
from registration import get_member
from models import Race
from store import store


def _new_race_id() -> str:
    return uuid.uuid4().hex[:8]


def create_race(name: str, location: str, prize_money: float) -> Race:
    if prize_money <= 0:
        raise ValueError("prize_money must be greater than 0")

    race = Race(
        race_id=_new_race_id(),
        name=name,
        location=location,
        prize_money=prize_money,
        status="upcoming",
        driver_id="",
        car_id="",
        winner_id="",
    )
    store.races[race.race_id] = race
    return race


def assign_driver_to_race(race_id: str, member_id: str) -> Race:
    race = get_race(race_id)
    member = get_member(member_id)

    if member.role != "driver":
        raise ValueError("Only drivers can be assigned to a race")
    if not member.is_available:
        raise ValueError("Driver is not available")

    race.driver_id = member_id
    set_availability(member_id, False)
    return race


def assign_car_to_race(race_id: str, car_id: str) -> Race:
    race = get_race(race_id)
    car = get_car(car_id)

    if not car.is_available:
        raise ValueError("Car is not available")
    if car.condition == "damaged":
        raise ValueError("Damaged car cannot be assigned to a race")

    race.car_id = car_id
    car.is_available = False
    return race


def start_race(race_id: str) -> Race:
    race = get_race(race_id)
    if not race.driver_id:
        raise ValueError("No driver assigned")
    if not race.car_id:
        raise ValueError("No car assigned")
    race.status = "in_progress"
    return race


def get_race(race_id: str) -> Race:
    return store.races[race_id]


def list_races(status_filter: str = None) -> list[Race]:
    races = list(store.races.values())
    if status_filter is None:
        return races
    return [race for race in races if race.status == status_filter]
