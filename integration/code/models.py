from dataclasses import dataclass, field
from typing import List


@dataclass
class CrewMember:
    member_id: str
    name: str
    role: str
    skill_level: int
    is_available: bool


@dataclass
class Car:
    car_id: str
    name: str
    speed_rating: int
    condition: str
    is_available: bool


@dataclass
class Race:
    race_id: str
    name: str
    location: str
    prize_money: float
    status: str
    driver_id: str
    car_id: str
    winner_id: str


@dataclass
class Mission:
    mission_id: str
    name: str
    mission_type: str
    required_roles: List[str]
    assigned_members: List[str]
    status: str
    requires_mechanic: bool


@dataclass
class InventoryItem:
    item_id: str
    item_type: str
    name: str
    quantity: int
