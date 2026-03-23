# DASS Assignment 2 Submission

This repository contains the three required parts of the assignment:

- `whitebox/`: MoneyPoly white-box testing
- `integration/`: StreetRace Manager integration testing
- `blackbox/`: QuickCart REST API black-box testing

## Repository Link

`https://github.com/Athmeeya2006/dass-assignment-2`

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

The folders and PDFs above are the intended submission artifacts. Some extra working files may still exist in the repository for development history, verification, or local tooling.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pylint requests pytest-html
```

## Whitebox: MoneyPoly

### Contents

- Code: `whitebox/code/moneypoly/`
- Tests: `whitebox/tests/`
- Diagrams folder: `whitebox/diagrams/`
- Final report: `whitebox/report.pdf`

### What Was Done

- Audited the internal MoneyPoly logic using white-box testing.
- Designed tests to cover decision branches, key variable states, and important edge cases.
- Fixed logical defects one by one using `Error #:` commits.
- Improved code quality iteratively using `Iteration #:` commits.
- Generated the final whitebox report as `whitebox/report.pdf`.

### Verified Status

- `python3 -m pytest whitebox/tests -q` -> `35 passed`
- `PYLINTHOME=/tmp/pylint .venv/bin/python -m pylint whitebox/code/moneypoly/main.py whitebox/code/moneypoly/moneypoly/*.py` -> `10.00/10`

### Main Issues Found And Fixed

- Dice originally used `1..5` instead of `1..6`.
- Passing Go did not always award salary correctly.
- Rent bonus logic accepted partial group ownership.
- Rent payment did not credit the owner correctly.
- Mortgage and unmortgage flows had state-consistency issues.
- Trade handling had validation and transfer issues.
- Jail fine handling had a balance deduction bug.
- Winner selection and net-worth calculation were incorrect.
- Bankruptcy could break turn order and doubles behavior.

### How To Run The Whitebox Code

```bash
cd whitebox/code/moneypoly
python3 main.py
```

### How To Run The Whitebox Tests

```bash
python3 -m pytest whitebox/tests -v
```

### Manual Item Still Needed

Add the hand-drawn control flow graph image to `whitebox/diagrams/`.

## Integration: StreetRace Manager

### Contents

- Code: `integration/code/`
- Tests: `integration/tests/`
- Diagrams folder: `integration/diagrams/`
- Final report: `integration/report.pdf`

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

### What Was Done

- Implemented and tested the StreetRace Manager modules.
- Verified module-to-module interaction instead of only isolated functionality.
- Designed integration tests around realistic workflows and business rules.
- Generated the final integration report as `integration/report.pdf`.

### Verified Status

- `python3 -m pytest integration/tests -q` -> `154 passed`

### Important Integration Rules Covered

- A crew member must be registered before system workflows can use that member.
- Only drivers can be entered into races.
- Unavailable drivers cannot be assigned to races.
- Damaged cars cannot enter races until repaired.
- Race results update both rankings and inventory cash balance.
- Missions fail when required roles are unavailable.
- Crew members reserved by races or missions are later released correctly.

### How To Run The Integration Code

```bash
cd integration/code
python3 main.py
```

### How To Run The Integration Tests

```bash
python3 -m pytest integration/tests -v
```

### Manual Item Still Needed

Add the hand-drawn call graph image to `integration/diagrams/`.

## Blackbox: QuickCart API

### Contents

- Tests: `blackbox/tests/`
- Final report: `blackbox/report.pdf`

### What Was Done

- Designed black-box tests directly from the QuickCart API documentation.
- Covered valid requests, invalid inputs, missing fields, wrong data types, and boundary values.
- Verified status codes, JSON structures, and returned data against the documented expectations.
- Recorded bug findings in the final blackbox report.

### Saved Execution Status

The checked-in blackbox artifacts report:

- `147` total test cases
- `130` passed
- `17` failed
- `1` skipped

### Main Bugs Documented

- Cart accepts zero and negative quantities.
- Cart subtotal and cart total calculations are incorrect.
- COD checkout is allowed above the documented limit.
- Wallet checkout succeeds with insufficient balance.
- Cancelling orders does not restore stock correctly.
- Address pincode validation is incomplete.
- Profile phone validation is incomplete.
- Review rating validation is incomplete.
- Wallet deduction has a precision problem.
- Non-existent user IDs return the wrong status code.

### How To Run The Blackbox Tests

Make sure the QuickCart API is running at `http://localhost:8080`.

```bash
python3 -m pytest blackbox/tests -v
```

If dependencies are needed:

```bash
pip install -r blackbox/requirements.txt
```

## Quick Verification Summary

- Whitebox tests: passing
- Whitebox pylint: clean
- Integration tests: passing
- Blackbox report and test suite: present
- Final PDFs: present in all three sections

## Final Submission Checklist

- Ensure `whitebox/report.pdf`, `integration/report.pdf`, and `blackbox/report.pdf` are present.
- Ensure the hand-drawn whitebox control flow graph is placed in `whitebox/diagrams/`.
- Ensure the hand-drawn integration call graph is placed in `integration/diagrams/`.
- Push the final repository state to GitHub.
