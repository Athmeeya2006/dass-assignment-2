from models import CrewMember
from registration import VALID_ROLES, get_member
from store import store


def assign_role(member_id: str, new_role: str) -> CrewMember:
    member = get_member(member_id)
    if new_role not in VALID_ROLES:
        raise ValueError("Invalid role")
    store.crew_members[member_id].role = new_role
    return store.crew_members[member_id]


def update_skill_level(member_id: str, skill_level: int) -> CrewMember:
    get_member(member_id)
    if not 1 <= skill_level <= 10:
        raise ValueError("Skill level must be 1-10")
    store.crew_members[member_id].skill_level = skill_level
    return store.crew_members[member_id]


def set_availability(member_id: str, is_available: bool) -> CrewMember:
    get_member(member_id)
    store.crew_members[member_id].is_available = is_available
    return store.crew_members[member_id]


def get_available_by_role(role: str) -> list[CrewMember]:
    return [
        member
        for member in store.crew_members.values()
        if member.role == role and member.is_available
    ]
