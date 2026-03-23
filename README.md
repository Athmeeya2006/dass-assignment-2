# DASS Assignment Submission

This repository contains the three required parts of the assignment:

- `whitebox/`: MoneyPoly white-box testing
- `integration/`: StreetRace Manager integration testing
- `blackbox/`: QuickCart REST API black-box testing

## Required Submission Structure

```text
whitebox/
  code/
  diagrams/
  tests/
  report.pdf
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

Note:

- Extra working files may still exist in the repository for development and
  verification, but the structure above is the intended submission layout.
- The hand-drawn diagram images must be placed in the corresponding
  `diagrams/` folders before final submission.

## Git Repository Link

Repository:
`https://github.com/Athmeeya2006/dass-assignment-2`

## Whitebox: MoneyPoly

MoneyPoly is a command-line board game that manages players, movement, money,
property purchases, rent, cards, jail logic, bankruptcy, and winner selection.

### Whitebox Deliverables

- Source code: `whitebox/code/moneypoly/`
- White-box tests: `whitebox/tests/`
- Diagram folder: `whitebox/diagrams/`
- Final report file for submission: `whitebox/report.pdf`

### Whitebox Work Completed

- White-box tests were designed around branches, variable states, and edge
  cases.
- Logical issues were fixed one by one using `Error #:` commits.
- Pylint cleanup was done iteratively using `Iteration #:` commits.
- Verified local status:
  - `python3 -m pytest whitebox/tests -q` -> `35 passed`
  - `PYLINTHOME=/tmp/pylint .venv/bin/python -m pylint whitebox/code/moneypoly/main.py whitebox/code/moneypoly/moneypoly/*.py`
    -> `10.00/10`

### Important Whitebox Findings

- Dice originally used `1..5` instead of `1..6`.
- Passing Go did not always pay salary.
- Group rent logic accepted partial ownership instead of full ownership.
- Bank loan and rent transfer logic had money-consistency issues.
- Exact-balance purchases, mortgage handling, trade validation, jail fine
  deduction, winner selection, and bankruptcy turn flow all required fixes.

### How To Run Whitebox Code

From the repository root:

```bash
cd whitebox/code/moneypoly
python3 main.py
```

### How To Run Whitebox Tests

From the repository root:

```bash
python3 -m pytest whitebox/tests -v
```

## Integration: StreetRace Manager

StreetRace Manager is a command-line system built module-by-module and then
tested for interaction between modules.

### Integration Deliverables

- Source code: `integration/code/`
- Integration tests: `integration/tests/`
- Diagram folder: `integration/diagrams/`
- Final report file for submission: `integration/report.pdf`

### Modules Implemented

Required modules:

- Registration
- Crew Management
- Inventory
- Race Management
- Results
- Mission Planning

Additional modules:

- Garage
- Leaderboard

### Verified Integration Status

- `python3 -m pytest integration/tests -q` -> `154 passed`

### Key Integration Rules Covered

- A crew member must be registered before a role can be assigned.
- Only crew members with the driver role may enter a race.
- Damaged-car scenarios require mechanic availability when relevant.
- Race results update rankings and inventory cash balance.
- Missions cannot start when required roles are unavailable.

### How To Run Integration Code

From the repository root:

```bash
cd integration/code
python3 main.py
```

### How To Run Integration Tests

From the repository root:

```bash
python3 -m pytest integration/tests -v
```

## Blackbox: QuickCart API

QuickCart was tested as a black-box REST API using `pytest` and `requests`.

### Blackbox Deliverables

- Automated tests: `blackbox/tests/`
- Final report file for submission: `blackbox/report.pdf`

### Blackbox Coverage

- Valid requests
- Invalid inputs
- Missing fields
- Wrong data types
- Boundary values
- HTTP status code checks
- JSON structure checks
- Returned data validation against the API specification

### Existing Bug Findings

The saved bug documentation reports issues such as:

- cart accepting zero or negative quantities
- incorrect subtotal and cart total calculations
- invalid checkout behavior for COD and wallet cases
- stock not being restored on order cancellation
- invalid address, phone, and review validation behavior
- wallet precision issues
- incorrect status code for non-existent user IDs

### How To Run Blackbox Tests

Make sure the QuickCart API is running at `http://localhost:8080`.

From the repository root:

```bash
python3 -m pytest blackbox/tests -v
```

If dependencies are needed:

```bash
pip install -r blackbox/requirements.txt
```

## Setup Notes

If you want a dedicated virtual environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pylint requests pytest-html
```

## Final Manual Items Before Submission

- Add the hand-drawn MoneyPoly control flow graph image to `whitebox/diagrams/`.
- Add the hand-drawn StreetRace Manager call graph image to
  `integration/diagrams/`.
- Ensure the final polished reports are exported as:
  - `whitebox/report.pdf`
  - `integration/report.pdf`
  - `blackbox/report.pdf`
