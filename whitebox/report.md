# MoneyPoly White-Box Testing Report

## Introduction

This report presents the white-box testing of the MoneyPoly board-game
implementation. The internal logic of the program was analyzed using
control-flow-based testing, branch testing, state-based testing, and edge-case
testing. The goal was to identify logical defects in player movement, money
handling, property transactions, card effects, jail logic, and game
termination.

## Program Overview

MoneyPoly is a command-line board game that manages players, money, board
movement, property purchasing, rent payment, taxes, chance and community chest
cards, jail behavior, bankruptcy, and winner selection.

## CFG

A hand-drawn control flow graph was prepared for the main execution path of the
program. The graph starts from player input and game initialization, then
follows the main game loop, turn execution, movement resolution, card handling,
jail processing, bankruptcy checking, and winner selection. The CFG includes
the most important branches that affect gameplay.

Add the hand-drawn CFG image at `whitebox/diagrams/control_flow_graph.jpg` or
update this reference to the final image path before submission.

## Pylint

Pylint was used iteratively to improve code quality. The main warnings included
unused imports, broad exception handling, boolean-style issues, formatting
inconsistencies, long lines, and missing documentation comments. These were
fixed step by step, and pylint was run again after each round. Each round of
code-quality improvement was saved as a separate commit using the required
iteration format.

Verified result:

- `python3 -m pytest whitebox/tests -q` -> `35 passed`
- `PYLINTHOME=/tmp/pylint .venv/bin/python -m pylint whitebox/code/moneypoly/main.py whitebox/code/moneypoly/moneypoly/*.py`
  -> `10.00/10`

## White-Box Testing Strategy

The white-box tests were designed from the internal structure of the code
rather than only from input and output behavior. Test cases were created to
cover important branches, key variable states, and relevant edge cases such as
empty decks, exact-balance purchases, invalid trades, passing Go, mortgage
failures, and bankruptcy. This helped reveal defects in movement logic, rent
handling, ownership checks, net-worth computation, and turn progression.

## Test Cases

`TC1` Board tile classification

- Why necessary: `_move_and_resolve()` depends on correct tile routing for game
  actions.
- Revealed issue: used as a branch safety check to confirm routing through `go`,
  `property`, `community_chest`, and `blank` tiles.

`TC2` Property purchasable branches

- Why necessary: `Board.is_purchasable()` has separate branches for unowned,
  owned, mortgaged, and non-property tiles.
- Revealed issue: catches incorrect purchasable-state handling for mortgaged or
  occupied properties.

`TC3` Board ownership helper methods

- Why necessary: ownership lists drive reporting and later ownership-dependent
  logic.
- Revealed issue: verifies owned and unowned property tracking stays consistent.

`TC4` Card deck normal cycle and empty deck safety

- Why necessary: card drawing is reused across Chance and Community Chest flows,
  including the empty-deck edge case.
- Revealed issue: the original code crashes on empty decks in
  `cards_remaining()` and `__repr__()`.

`TC5` Single-player and duplicate-name setup rejection

- Why necessary: the game requires at least two unique players for valid turn
  flow and ownership reporting.
- Revealed issue: the original setup accepted too few players and duplicate
  names.

`TC6` Dice full range

- Why necessary: every movement path depends on correct six-sided dice
  behaviour.
- Revealed issue: the original dice used `1..5` instead of `1..6`.

`TC7` Passing Go salary

- Why necessary: passing the board boundary is a key money-state transition.
- Revealed issue: salary was only awarded when landing exactly on Go.

`TC8` Full color-group ownership

- Why necessary: rent multipliers depend on owning an entire group, not a
  partial subset.
- Revealed issue: group ownership originally used partial-ownership logic.

`TC9` Bank loan accounting and collect/payout guards

- Why necessary: bank operations must preserve money consistency.
- Revealed issue: loan issuance originally increased player money without
  reducing bank reserves, and negative `collect()` values were accepted.

`TC10` Exact-balance purchase and invalid purchase rejection

- Why necessary: property purchases need safe handling at the affordability
  boundary and for invalid direct calls.
- Revealed issue: exact-balance purchases were rejected, and owned or mortgaged
  properties could be bought directly.

`TC11` Rent transfer

- Why necessary: rent is a two-party transaction and must update both balances.
- Revealed issue: rent was deducted from the tenant but not credited to the
  owner.

`TC12` Unmortgage and mortgage failure consistency

- Why necessary: property state must not change before affordability or bank
  funding checks succeed.
- Revealed issue: unmortgage cleared the mortgage before validating funds, and
  mortgage could partially succeed when the bank could not cover the payout.

`TC13` Trade validation and transfer

- Why necessary: trades affect balances, ownership, and player inventories.
- Revealed issue: the original trade flow did not credit the seller and allowed
  invalid cases such as negative cash and self-trade.

`TC14` Jail fine handling

- Why necessary: jail release is a branch with direct money-state impact.
- Revealed issue: voluntary release credited the bank without deducting the
  player's balance.

`TC15` Property tile choice branches

- Why necessary: `_handle_property_tile()` contains buy, auction, skip,
  self-owned, and opponent-owned paths.
- Revealed issue: confirms that the decision routing reaches the correct action
  handler for each branch.

`TC16` Special tile routing

- Why necessary: `go_to_jail`, tax, and free-parking branches are major
  decision paths in `_move_and_resolve()`.
- Revealed issue: verifies money changes and jail state transitions for special
  tiles.

`TC17` Card action branches

- Why necessary: `_apply_card()` contains multiple internal branches driven by
  action type and player balance.
- Revealed issue: validates `collect`, `pay`, `jail`, `jail_free`, `move_to`,
  `birthday`, and `collect_from_all`, including the poor-player skip branch.

`TC18` Railroad and property routing

- Why necessary: railroad and property tiles must resolve to actual property
  objects and handler calls.
- Revealed issue: railroad positions originally had no property objects, so the
  railroad branch could not function.

`TC19` Bankruptcy cleanup

- Why necessary: bankruptcy is a major state transition that affects players,
  properties, and turn order.
- Revealed issue: validates player removal and property reset behaviour.

`TC20` Net worth and winner selection

- Why necessary: standings and final winner selection depend on accurate asset
  valuation.
- Revealed issue: `net_worth()` ignored property values and winner selection
  used the poorest player.

`TC21` Auction validation

- Why necessary: auctions should not proceed for invalid property states.
- Revealed issue: owned or mortgaged properties were not rejected before
  auction.

`TC22` Interactive menu reachability

- Why necessary: the pre-roll menu is part of the intended gameplay flow.
- Revealed issue: the menu existed but was never called from `play_turn()`.

`TC23` Turn order after bankruptcy

- Why necessary: removing the current player during a turn can corrupt index
  advancement and doubles behaviour.
- Revealed issue: bankruptcy could skip the next player or incorrectly preserve
  an extra turn.

## Conclusion

The white-box testing process revealed multiple logical problems in the
MoneyPoly implementation. The most serious issues affected financial
consistency, ownership handling, net-worth calculation, and turn progression.
By using branch coverage, state-based testing, and boundary testing, these
defects were identified and corrected in a structured manner.

## Notes

- The CFG image still needs to be created by hand and attached at the final
  submission path referenced above.
- The automated Git helper is available at
  `whitebox/scripts/auto_git_push.py` for minute-by-minute commit and push
  automation.

## Repository Audit

This section records a final audit of the repository against the assignment
brief so the submission state is clear.

### Whitebox Status

- Implementation under test is present in `whitebox/code/moneypoly/`.
- White-box tests are present in `whitebox/tests/`.
- Verification was rerun locally and passed:
  `python3 -m pytest whitebox/tests -q` -> `35 passed`.
- Pylint was rerun locally and passed:
  `PYLINTHOME=/tmp/pylint .venv/bin/python -m pylint whitebox/code/moneypoly/main.py whitebox/code/moneypoly/moneypoly/*.py`
  -> `10.00/10`.
- Required commit workflow was completed with `test1`, `Error #:` commits, and
  `Iteration #:` commits.
- Remaining manual item:
  the assignment requires a hand-drawn CFG image, and that image is still not
  included in the repository.

### Integration Status

- StreetRace Manager source modules are present in `integration/code/`.
- At least two extra modules are present:
  `garage.py` and `leaderboard.py`.
- Integration and module tests were rerun locally and passed:
  `python3 -m pytest integration/tests -q` -> `154 passed`.
- Call-graph source material is present in
  `integration/diagrams/integration_call_graph.mmd` and
  `integration/diagrams/call_graph_description.md`.
- Existing report artifacts are present:
  `integration/report.pdf` and `integration/test_report.html`.
- Remaining manual item:
  the assignment asks for a hand-drawn call-graph image, but the repository
  currently contains graph source/description files rather than the final image
  itself.

### Blackbox Status

- QuickCart automated API tests are present in `blackbox/tests/`.
- Existing result artifacts are present:
  `blackbox/report.html`, `blackbox/report.pdf`, and
  `blackbox/bug_reports/bugs.md`.
- The existing HTML report shows a previous run with
  `147 tests`, `130 passed`, `17 failed`, and `1 skipped`.
- The bug report captures verified issues and affected endpoints.
- Current environment limitation:
  a live rerun could not be completed during this audit because requests to
  `http://localhost:8080/api/v1/...` fail in the sandbox with connection
  errors, so blackbox behavior could only be audited from the checked-in test
  suite and saved report artifacts.
- Documentation gap to review before final submission:
  the assignment asks each bug report to include method, URL, headers, and body
  for the request payload. The checked-in `blackbox/bug_reports/bugs.md` lists
  endpoints and observed behavior clearly, but those payload fields should be
  checked against the final required format before submission.

### Overall Audit Result

- Whitebox code and tests are in good submission shape, pending the manual CFG
  image.
- Integration code and tests are in good submission shape, pending the manual
  call-graph image.
- Blackbox artifacts exist, but live execution could not be re-verified in this
  sandbox, and the bug-report formatting should be checked one more time
  against the assignment wording.
