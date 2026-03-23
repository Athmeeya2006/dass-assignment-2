import uuid

from crew_management import get_available_by_role, set_availability
from models import Mission
from registration import VALID_ROLES
from store import store


VALID_MISSION_TYPES = ["delivery", "rescue", "surveillance"]


def _new_mission_id() -> str:
    return uuid.uuid4().hex[:8]


def create_mission(
    name: str,
    mission_type: str,
    required_roles: list[str],
    involves_damaged_car: bool = False,
) -> Mission:
    if mission_type not in VALID_MISSION_TYPES:
        raise ValueError("Invalid mission type")
    if not required_roles:
        raise ValueError("required_roles must be non-empty")
    if any(role not in VALID_ROLES for role in required_roles):
        raise ValueError("Invalid required role")

    mission = Mission(
        mission_id=_new_mission_id(),
        name=name,
        mission_type=mission_type,
        required_roles=required_roles,
        assigned_members=[],
        status="planned",
        requires_mechanic=involves_damaged_car,
    )
    store.missions[mission.mission_id] = mission
    return mission


def assign_mission(mission_id: str) -> Mission:
    mission = get_mission(mission_id)

    selected_member_ids: list[str] = []
    for role in mission.required_roles:
        candidates = get_available_by_role(role)
        candidates = [member for member in candidates if member.member_id not in selected_member_ids]
        if not candidates:
            raise ValueError(f"Mission failed: no available {role}")
        selected_member_ids.append(candidates[0].member_id)

    if mission.requires_mechanic:
        mechanics = get_available_by_role("mechanic")
        mechanics = [m for m in mechanics if m.member_id not in selected_member_ids]
        if not mechanics:
            raise ValueError("Mission failed: damaged car requires available mechanic")

    mission.assigned_members = []
    for member_id in selected_member_ids:
        set_availability(member_id, False)
        mission.assigned_members.append(member_id)

    mission.status = "active"
    return mission


def complete_mission(mission_id: str) -> Mission:
    mission = get_mission(mission_id)
    mission.status = "completed"
    for member_id in mission.assigned_members:
        set_availability(member_id, True)
    return mission


def fail_mission(mission_id: str, reason: str) -> Mission:
    _ = reason
    mission = get_mission(mission_id)
    mission.status = "failed"
    for member_id in mission.assigned_members:
        set_availability(member_id, True)
    return mission


def get_mission(mission_id: str) -> Mission:
    return store.missions[mission_id]
