from crew_management import set_availability
from inventory import add_cash, update_car_condition
from race_management import get_race
from registration import get_member
from store import store


def record_result(race_id: str, winner_id: str, car_condition_after: str):
    race = get_race(race_id)
    if race.status != "in_progress":
        raise ValueError("Race is not in progress")
    if winner_id != race.driver_id:
        raise ValueError("Winner must be the assigned driver")

    race.winner_id = winner_id
    race.status = "completed"

    add_cash(race.prize_money)
    update_car_condition(race.car_id, car_condition_after)
    store.cars[race.car_id].is_available = True
    set_availability(race.driver_id, True)

    ranking_entry = None
    for entry in store.race_rankings:
        if entry["member_id"] == winner_id:
            ranking_entry = entry
            break

    if ranking_entry is None:
        ranking_entry = {"member_id": winner_id, "wins": 0, "earnings": 0.0}
        store.race_rankings.append(ranking_entry)

    ranking_entry["wins"] += 1
    ranking_entry["earnings"] += race.prize_money
    return race


def get_rankings() -> list[dict]:
    return sorted(
        store.race_rankings,
        key=lambda item: (item["wins"], item["earnings"]),
        reverse=True,
    )


def get_driver_stats(member_id: str) -> dict:
    for entry in store.race_rankings:
        if entry["member_id"] == member_id:
            member = get_member(member_id)
            return {
                "member_id": member_id,
                "name": member.name,
                "wins": entry["wins"],
                "earnings": entry["earnings"],
            }
    raise KeyError(member_id)
