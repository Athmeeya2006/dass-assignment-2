import uuid

from models import CrewMember
from store import store


VALID_ROLES = ["driver", "mechanic", "strategist", "navigator"]


def _new_member_id() -> str:
    return uuid.uuid4().hex[:8]


def register_member(name: str, role: str) -> CrewMember:
    if not 2 <= len(name) <= 50:
        raise ValueError("Name must be 2-50 characters")
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")

    member = CrewMember(
        member_id=_new_member_id(),
        name=name,
        role=role,
        skill_level=1,
        is_available=True,
    )
    store.crew_members[member.member_id] = member
    return member


def get_member(member_id: str) -> CrewMember:
    if member_id not in store.crew_members:
        raise KeyError(f"Member {member_id} not found")
    return store.crew_members[member_id]


def list_members() -> list[CrewMember]:
    return list(store.crew_members.values())


def remove_member(member_id: str) -> bool:
    if member_id not in store.crew_members:
        raise KeyError(f"Member {member_id} not found")
    del store.crew_members[member_id]
    return True
