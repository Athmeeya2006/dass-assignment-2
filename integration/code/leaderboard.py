from registration import get_member
from results import get_rankings
from store import store


def get_full_leaderboard() -> list[dict]:
    enriched: list[dict] = []
    for entry in get_rankings():
        try:
            name = get_member(entry["member_id"]).name
        except KeyError:
            name = "Unknown"
        enriched.append(
            {
                "member_id": entry["member_id"],
                "name": name,
                "wins": entry["wins"],
                "earnings": entry["earnings"],
            }
        )
    return sorted(enriched, key=lambda item: (item["wins"], item["earnings"]), reverse=True)


def get_top_driver(n: int = 3) -> list[dict]:
    return get_full_leaderboard()[:n]


def get_mission_success_rate() -> dict:
    missions = list(store.missions.values())
    total = len(missions)
    completed = sum(1 for mission in missions if mission.status == "completed")
    failed = sum(1 for mission in missions if mission.status == "failed")
    success_rate = (completed / total * 100.0) if total else 0.0
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "success_rate_percent": success_rate,
    }
