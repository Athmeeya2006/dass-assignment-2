# Call Graph — StreetRace Manager

## System Architecture

The StreetRace Manager system consists of 9 modules that interact through a central Store singleton. All modules are stateless and delegate to the Store for in-memory state management.

---

## Within-Module Calls

### registration.py
- `register_member()` → creates CrewMember dataclass, stores in `store.crew_members`
- `get_member()` → retrieves from `store.crew_members` by ID
- `list_members()` → returns `list(store.crew_members.values())`
- `remove_member()` → deletes from `store.crew_members`

### crew_management.py
- `assign_role()` → calls `registration.get_member()` to validate, updates `store.crew_members[id].role`
- `update_skill_level()` → calls `registration.get_member()` to validate, updates `store.crew_members[id].skill_level`
- `set_availability()` → calls `registration.get_member()` to validate, updates `store.crew_members[id].is_available`
- `get_available_by_role()` → filters `store.crew_members.values()` by role and is_available

### inventory.py
- `add_car()` → creates Car dataclass, stores in `store.cars`
- `get_car()` → retrieves from `store.cars` by ID
- `list_cars()` → returns filtered `list(store.cars.values())`
- `update_car_condition()` → calls `get_car()`, updates `store.cars[id].condition`
- `add_inventory_item()` → creates InventoryItem, stores in `store.inventory_items`
- `get_cash_balance()` → returns `store.cash_balance`
- `add_cash()` → updates `store.cash_balance` (increment)
- `deduct_cash()` → updates `store.cash_balance` (decrement)

### race_management.py
- `create_race()` → creates Race dataclass, stores in `store.races`
- `get_race()` → retrieves from `store.races` by ID
- `list_races()` → returns filtered `list(store.races.values())`
- `assign_driver_to_race()` → calls `get_race()`, updates `store.races[id].driver_id`
- `assign_car_to_race()` → calls `get_race()`, updates `store.races[id].car_id` and `store.cars[id].is_available`
- `start_race()` → calls `get_race()`, updates `store.races[id].status`

### results.py
- `record_result()` → calls `race_management.get_race()`, updates `store.races[id]` with result
- `get_rankings()` → returns sorted `store.race_rankings`
- `get_driver_stats()` → searches `store.race_rankings` for entry, calls `registration.get_member()` for name enrichment

### mission_planning.py
- `create_mission()` → creates Mission dataclass, stores in `store.missions`
- `get_mission()` → retrieves from `store.missions` by ID
- `assign_mission()` → calls `get_mission()`, updates `store.missions[id].assigned_members` and `store.missions[id].status`
- `complete_mission()` → calls `get_mission()`, updates `store.missions[id].status`
- `fail_mission()` → calls `get_mission()`, updates `store.missions[id].status`

### leaderboard.py
- `get_full_leaderboard()` → calls `results.get_rankings()`, enrich with member names from `registration.get_member()`
- `get_top_driver()` → calls `get_full_leaderboard()`, slices result
- `get_mission_success_rate()` → analyzes `store.missions` for status counts

### garage.py
- `repair_car()` → calls `inventory.get_car()` and `registration.get_member()`, updates `store.cars[id].condition`
- `get_repair_log()` → returns `store.repair_log`
- `get_cars_needing_repair()` → filters `store.cars.values()` by condition == "damaged"

---

## Cross-Module Calls (Integration Points)

### `race_management.assign_driver_to_race()`
- **Calls:**
  - `registration.get_member(member_id)` → verify driver exists
  - `crew_management.set_availability(member_id, False)` → mark driver unavailable
- **Updates:**
  - `store.races[race_id].driver_id = member_id`

### `race_management.assign_car_to_race()`
- **Calls:**
  - `inventory.get_car(car_id)` → verify car exists and get its state
- **Updates:**
  - `store.races[race_id].car_id = car_id`
  - `store.cars[car_id].is_available = False`

### `results.record_result()`
- **Calls:**
  - `race_management.get_race(race_id)` → verify race exists and get state
  - `inventory.add_cash(race.prize_money)` → add prize to balance
  - `inventory.update_car_condition(car_id, condition)` → update car after race
  - `crew_management.set_availability(driver_id, True)` → free driver
- **Updates:**
  - `store.races[race_id].status = "completed"`
  - `store.races[race_id].winner_id = member_id`
  - `store.cash_balance += prize_money`
  - `store.cars[car_id].condition = new_condition`
  - `store.cars[car_id].is_available = True`
  - `store.race_rankings` → find/create entry for driver, increment wins, add earnings
  - `store.crew_members[driver_id].is_available = True`

### `mission_planning.assign_mission()`
- **Calls:**
  - `crew_management.get_available_by_role(role)` → find available candidates for each role
  - `crew_management.set_availability(member_id, False)` → mark each assigned member unavailable (once per member)
- **Updates:**
  - `store.missions[mission_id].assigned_members = [member_ids]`
  - `store.missions[mission_id].status = "active"`
  - For each assigned member: `store.crew_members[id].is_available = False`

### `mission_planning.complete_mission()` and `fail_mission()`
- **Calls:**
  - `crew_management.set_availability(member_id, True)` → free each assigned member (once per member)
- **Updates:**
  - `store.missions[mission_id].status = "completed"` or `"failed"`
  - For each assigned member: `store.crew_members[id].is_available = True`

### `garage.repair_car()`
- **Calls:**
  - `inventory.get_car(car_id)` → verify car exists
  - `registration.get_member(mechanic_id)` → verify mechanic exists
  - `inventory.update_car_condition(car_id, "good")` → set condition to good
- **Updates:**
  - `store.cars[car_id].condition = "good"`
  - `store.repair_log` → append entry with car_id, mechanic_id, timestamp

### `leaderboard.get_full_leaderboard()`
- **Calls:**
  - `results.get_rankings()` → get sorted race rankings
  - For each entry: `registration.get_member(member_id)` → retrieve driver name
- **Returns:**
  - Enriched rankings with member names, sorted by (wins DESC, earnings DESC)

---

## Data Flow Summary

**Race Completion Flow:**
```
race_management.start_race()
  → Race status = "in_progress"

results.record_result()
  → Calls race_management.get_race()
  → Calls inventory.add_cash(prize_money)
  → Calls inventory.update_car_condition()
  → Calls crew_management.set_availability(driver, available=True)
  → Updates store.race_rankings
  → Race status = "completed"
```

**Mission Assignment Flow:**
```
mission_planning.assign_mission()
  → For each required role:
      Calls crew_management.get_available_by_role(role)
      Calls crew_management.set_availability(member, False)
  → If involves_damaged_car:
      Calls crew_management.get_available_by_role("mechanic")
      Calls crew_management.set_availability(mechanic, False)
  → Mission status = "active"
```

**Garage Repair Flow:**
```
garage.repair_car()
  → Calls inventory.get_car(car_id)
  → Calls registration.get_member(mechanic_id)
  → Calls inventory.update_car_condition(car_id, "good")
  → Appends to store.repair_log
```

---

## Module Dependencies (arrows point to called modules)

```
registration.py
    ↓ (used by)
├─→ crew_management.py
├─→ race_management.py
├─→ results.py
├─→ leaderboard.py
└─→ garage.py

crew_management.py
    ↓ (used by)
├─→ race_management.py
├─→ results.py
├─→ mission_planning.py
└─→ leaderboard.py

inventory.py
    ↓ (used by)
├─→ race_management.py
├─→ results.py
└─→ garage.py

race_management.py
    ↓ (used by)
├─→ results.py
└─→ (called by main.py)

results.py
    ↓ (used by)
├─→ leaderboard.py
└─→ (called by main.py)

mission_planning.py
    ↓ (used by)
├─→ leaderboard.py (indirectly for mission success rate)
└─→ (called by main.py)

leaderboard.py
    ↓ (used by)
└─→ (called by main.py)

garage.py
    ↓ (used by)
└─→ (called by main.py)

store.py
    ↓ (used by ALL modules)
    └─→ Central singleton shared by all modules
```

---

## Key Architectural Patterns

1. **No Direct Module Imports:** Modules do NOT import each other's internals. All cross-module communication flows through Store or return values.

2. **Single Responsibility:** Each module manages one domain (registration, crew management, inventory, races, results, missions, leaderboard, garage).

3. **Validation Layer:** Each module validates its inputs by calling peer modules' `get_*` functions (e.g., `race_management` calls `registration.get_member()`).

4. **State Centralization:** All mutable state lives in `store.py`. Modules are stateless factories and coordinators.

5. **Availability Management:** A two-state flag (`is_available`) prevents double-booking of crew members across races and missions.

---

## Testing Coverage

- **Unit Tests:** Each module has 10+ tests covering happy paths, boundaries, and error cases.
- **Integration Tests:** 12+ scenarios test cross-module workflows (full race pipelines, mission-race conflicts, etc.).
- **Fixture-Based Reset:** Every test starts with a clean store via `conftest.py` autouse fixture.

- `garage.py`
- `repair_car()` -> validates mechanic/car -> updates car condition -> appends to `store.repair_log`
- `get_repair_log()` -> returns `store.repair_log`
- `get_cars_needing_repair()` -> filters `store.cars`

- `main.py`
- `run_cli()` -> dispatches to module menus
- Each menu (`registration_menu`, `crew_menu`, `inventory_menu`, `races_menu`, `results_menu`, `missions_menu`, `leaderboard_menu`, `garage_menu`) -> calls corresponding module functions via `safe_call()`

### Cross-Module Calls (Integration Arrows)
- `crew_management.assign_role()` -> `registration.get_member()`
- `crew_management.update_skill_level()` -> `registration.get_member()`
- `crew_management.set_availability()` -> `registration.get_member()`

- `race_management.assign_driver_to_race()`
- -> `race_management.get_race()`
- -> `registration.get_member()`
- -> `crew_management.set_availability()`

- `race_management.assign_car_to_race()`
- -> `race_management.get_race()`
- -> `inventory.get_car()`

- `results.record_result()`
- -> `race_management.get_race()`
- -> `inventory.add_cash()`
- -> `inventory.update_car_condition()`
- -> `crew_management.set_availability()`

- `results.get_driver_stats()`
- -> `registration.get_member()`

- `mission_planning.assign_mission()`
- -> `mission_planning.get_mission()`
- -> `crew_management.get_available_by_role()` (for each required role)
- -> `crew_management.get_available_by_role("mechanic")` when `requires_mechanic` is `True`
- -> `crew_management.set_availability()` (for each assigned member)

- `mission_planning.complete_mission()`
- -> `mission_planning.get_mission()`
- -> `crew_management.set_availability()`

- `mission_planning.fail_mission()`
- -> `mission_planning.get_mission()`
- -> `crew_management.set_availability()`

- `leaderboard.get_full_leaderboard()`
- -> `results.get_rankings()`
- -> `registration.get_member()` (for each ranking entry)

- `garage.repair_car()`
- -> `inventory.get_car()`
- -> `registration.get_member()`
- -> `crew_management.set_availability()` (set False then True)

### CLI-to-Module Call Paths (for Hand Drawing)
- `main.registration_menu()` -> `registration.register_member/get_member/list_members/remove_member`
- `main.crew_menu()` -> `crew_management.assign_role/update_skill_level/set_availability/get_available_by_role`
- `main.inventory_menu()` -> `inventory.add_car/get_car/list_cars/update_car_condition/add_inventory_item/get_cash_balance/add_cash/deduct_cash`
- `main.races_menu()` -> `race_management.create_race/assign_driver_to_race/assign_car_to_race/start_race/get_race/list_races`
- `main.results_menu()` -> `results.record_result/get_rankings/get_driver_stats`
- `main.missions_menu()` -> `mission_planning.create_mission/assign_mission/complete_mission/fail_mission/get_mission`
- `main.leaderboard_menu()` -> `leaderboard.get_full_leaderboard/get_top_driver/get_mission_success_rate`
- `main.garage_menu()` -> `garage.repair_car/get_repair_log/get_cars_needing_repair`

### Data-Flow Notes for Diagram Labels
- Shared singleton state hub: `store.py` (`store` object)
- All modules read/write the same in-memory dictionaries/lists through `store`
- Ranking updates originate in `results.record_result()` and are consumed by `leaderboard`
- Mission status updates originate in `mission_planning`, consumed by `leaderboard.get_mission_success_rate()`
- Repair events originate in `garage.repair_car()` and are stored in `store.repair_log`
