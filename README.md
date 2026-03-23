# StreetRace Manager + QuickCart Testing Submission

This repository contains coursework for two completed parts:
- `integration/`: StreetRace Manager integration design, implementation, and tests
- `blackbox/`: QuickCart REST API black-box automated tests

Whitebox testing is still pending and will be added later under `whitebox/`.

## Current Submission Structure

```text
integration/
  diagrams/
  tests/
  code/
  report.pdf
blackbox/
  tests/
  report.pdf
README.md
```

## StreetRace Manager (Integration)

The command-line StreetRace Manager system is implemented module-by-module and integrated in `integration/code/`.

Required modules implemented:
- Registration module
- Crew Management module
- Inventory module
- Race Management module
- Results module
- Mission Planning module

Additional modules implemented:
- Leaderboard module
- Garage module

### Key Business Rules Covered

- A crew member must be registered before role assignment.
- Only crew members with driver role can be entered in races.
- Mission assignment validates required crew roles and availability.
- Damaged-car scenarios are validated against mechanic availability.
- Race outcomes update ranking and inventory cash balance.

### Call Graph

- Call graph artifacts are stored in `integration/diagrams/`.
- The call graph includes function-level calls within and across modules.

### Integration Test Design

Integration tests are in `integration/tests/` and validate data flow and module interactions, including:
- Registering a driver and entering the driver into a race.
- Preventing race entry for invalid or unregistered drivers.
- Recording race results and verifying ranking and inventory updates.
- Mission assignment with role-availability validation.

## Black-Box API Testing (QuickCart)

Automated API tests are in `blackbox/tests/` and are written using `pytest` + `requests`.

Test coverage includes:
- Valid API requests
- Invalid input handling
- Missing-field behavior
- Wrong data types
- Boundary-value behavior
- HTTP status code validation
- JSON response structure validation
- Data correctness checks against API documentation

Bug findings are documented in the report and supporting notes under `blackbox/`.

## How To Run

### 1) Run StreetRace Manager CLI

From repository root:

```bash
cd integration/code
python main.py
```

### 2) Run Integration Tests

From repository root:

```bash
pip install -r integration/requirements.txt
pytest integration/tests -v
```

### 3) Run Black-Box Tests

Make sure the QuickCart API is running and reachable at `http://localhost:8080`.

From repository root:

```bash
pip install -r blackbox/requirements.txt
pytest blackbox/tests -v
```

## Git Repository Link

- Add your GitHub repository URL here: `https://github.com/<your-username>/<your-repo>`

## Status

- Completed: `integration/`, `blackbox/`
- Pending: `whitebox/`
