import pytest

from moneypoly import ui
from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.config import (
    GO_SALARY,
    INCOME_TAX_AMOUNT,
    JAIL_FINE,
    LUXURY_TAX_AMOUNT,
)
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


def test_board_tile_type_and_purchasable_branches():
    board = Board()
    mediterranean = board.get_property_at(1)

    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(2) == "community_chest"
    assert board.get_tile_type(12) == "blank"

    assert board.is_purchasable(1) is True
    mediterranean.owner = Player("Owner")
    assert board.is_purchasable(1) is False
    mediterranean.owner = None
    mediterranean.is_mortgaged = True
    assert board.is_purchasable(1) is False
    assert board.is_purchasable(12) is False


def test_board_ownership_helpers_track_owned_and_unowned_properties():
    board = Board()
    owner = Player("Owner")
    first = board.get_property_at(1)
    second = board.get_property_at(3)
    first.owner = owner
    second.owner = owner

    owned = board.properties_owned_by(owner)
    unowned = board.unowned_properties()

    assert first in owned and second in owned
    assert first not in unowned and second not in unowned


def test_card_deck_cycles_and_handles_empty_deck():
    deck = CardDeck([{"description": "A"}, {"description": "B"}])

    assert deck.peek()["description"] == "A"
    assert deck.draw()["description"] == "A"
    assert deck.draw()["description"] == "B"
    assert deck.draw()["description"] == "A"

    empty = CardDeck([])
    assert empty.draw() is None
    assert empty.peek() is None
    assert empty.cards_remaining() == 0
    assert repr(empty) == "CardDeck(0 cards, next=0)"


def test_game_requires_at_least_two_unique_players():
    with pytest.raises(ValueError):
        Game(["Solo"])

    with pytest.raises(ValueError):
        Game(["Asha", "Asha"])


def test_dice_roll_uses_full_six_sided_range(monkeypatch):
    calls = []

    def fake_randint(start, end):
        calls.append((start, end))
        return 6

    monkeypatch.setattr("moneypoly.dice.random.randint", fake_randint)

    dice = Dice()
    assert dice.roll() == 12
    assert calls == [(1, 6), (1, 6)]
    assert dice.is_doubles() is True


def test_player_move_collects_salary_when_passing_go():
    player = Player("Asha")
    player.position = 39

    new_position = player.move(3)

    assert new_position == 2
    assert player.balance == 1500 + GO_SALARY


def test_property_group_requires_full_set_for_bonus_rent():
    group = PropertyGroup("Brown", "brown")
    owner = Player("Owner")
    outsider = Player("Outsider")
    first = Property("Mediterranean Avenue", 1, 60, 2, group)
    second = Property("Baltic Avenue", 3, 60, 4, group)

    first.owner = owner
    second.owner = outsider

    assert group.all_owned_by(owner) is False
    assert first.get_rent() == 2


def test_bank_give_loan_reduces_bank_reserves():
    bank = Bank()
    player = Player("Asha")
    starting_bank = bank.get_balance()
    starting_player = player.balance

    bank.give_loan(player, 125)

    assert player.balance == starting_player + 125
    assert bank.get_balance() == starting_bank - 125


def test_bank_collect_and_pay_out_guards():
    bank = Bank()
    start_balance = bank.get_balance()

    bank.collect(-10)
    assert bank.get_balance() == start_balance

    assert bank.pay_out(0) == 0
    with pytest.raises(ValueError):
        bank.pay_out(start_balance + 1)


def test_buy_property_allows_spending_entire_balance():
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    player.balance = prop.price

    bought = game.buy_property(player, prop)

    assert bought is True
    assert prop.owner == player
    assert player.balance == 0


def test_buy_property_rejects_owned_or_mortgaged_property():
    game = Game(["Asha", "Ben"])
    buyer = game.players[1]
    owner = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = owner

    assert game.buy_property(buyer, prop) is False

    prop.owner = None
    prop.is_mortgaged = True
    assert game.buy_property(buyer, prop) is False


def test_pay_rent_transfers_money_to_owner():
    game = Game(["Asha", "Ben"])
    tenant, owner = game.players
    prop = game.board.get_property_at(1)
    prop.group = None
    prop.owner = owner
    owner.add_property(prop)
    tenant_start = tenant.balance
    owner_start = owner.balance

    game.pay_rent(tenant, prop)

    assert tenant.balance == tenant_start - prop.base_rent
    assert owner.balance == owner_start + prop.base_rent


def test_unmortgage_property_stays_mortgaged_when_player_cannot_afford():
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    prop.is_mortgaged = True
    player.balance = 1

    success = game.unmortgage_property(player, prop)

    assert success is False
    assert prop.is_mortgaged is True


def test_trade_transfers_cash_to_seller_and_property_to_buyer():
    game = Game(["Asha", "Ben"])
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)
    seller_start = seller.balance
    buyer_start = buyer.balance

    success = game.trade(seller, buyer, prop, 200)

    assert success is True
    assert prop.owner == buyer
    assert prop not in seller.properties
    assert prop in buyer.properties
    assert seller.balance == seller_start + 200
    assert buyer.balance == buyer_start - 200


def test_trade_rejects_negative_cash_and_self_trade():
    game = Game(["Asha", "Ben"])
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, -10) is False
    assert game.trade(seller, seller, prop, 10) is False


def test_handle_jail_turn_deducts_player_when_paying_fine(monkeypatch):
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    player.go_to_jail()
    start_balance = player.balance
    start_bank = game.bank.get_balance()

    monkeypatch.setattr("moneypoly.game.ui.confirm", lambda prompt: True)
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    move_calls = []
    monkeypatch.setattr(
        game,
        "_move_and_resolve",
        lambda p, steps: move_calls.append((p, steps)),
    )

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.balance == start_balance - JAIL_FINE
    assert game.bank.get_balance() == start_bank + JAIL_FINE
    assert move_calls == [(player, 4)]


def test_handle_property_tile_routes_buy_auction_skip_and_rent(monkeypatch):
    game = Game(["Asha", "Ben"])
    player, owner = game.players
    prop = game.board.get_property_at(1)
    actions = []

    monkeypatch.setattr("builtins.input", lambda prompt: "b")
    monkeypatch.setattr(
        game,
        "buy_property",
        lambda p, current_prop: actions.append(("buy", p.name, current_prop.name)),
    )
    game._handle_property_tile(player, prop)

    monkeypatch.setattr("builtins.input", lambda prompt: "a")
    monkeypatch.setattr(
        game,
        "auction_property",
        lambda current_prop: actions.append(("auction", current_prop.name)),
    )
    game._handle_property_tile(player, prop)

    monkeypatch.setattr("builtins.input", lambda prompt: "s")
    game._handle_property_tile(player, prop)

    prop.owner = player
    game._handle_property_tile(player, prop)

    prop.owner = owner
    monkeypatch.setattr(
        game,
        "pay_rent",
        lambda p, current_prop: actions.append(("rent", p.name, current_prop.name)),
    )
    game._handle_property_tile(player, prop)

    assert actions == [
        ("buy", "Asha", prop.name),
        ("auction", prop.name),
        ("rent", "Asha", prop.name),
    ]


def test_mortgage_property_stays_consistent_when_bank_cannot_pay():
    game = Game(["Asha", "Ben"])
    game.bank._funds = 10
    player = game.players[0]
    prop = game.board.get_property_at(39)
    prop.owner = player
    player.add_property(prop)
    start_balance = player.balance

    success = game.mortgage_property(player, prop)

    assert success is False
    assert prop.is_mortgaged is False
    assert player.balance == start_balance
    assert game.bank.get_balance() == 10


@pytest.mark.parametrize(
    ("tile", "position", "expected_bank_delta"),
    [
        ("go_to_jail", 30, 0),
        ("income_tax", 4, INCOME_TAX_AMOUNT),
        ("luxury_tax", 38, LUXURY_TAX_AMOUNT),
        ("free_parking", 20, 0),
    ],
)
def test_move_and_resolve_special_tiles(
    tile,
    position,
    expected_bank_delta,
    monkeypatch,
):
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    start_bank = game.bank.get_balance()

    def fake_move(steps):
        player.position = position
        return position

    monkeypatch.setattr(player, "move", fake_move)

    game._move_and_resolve(player, 3)

    assert game.board.get_tile_type(position) == tile
    assert game.bank.get_balance() == start_bank + expected_bank_delta
    if tile == "go_to_jail":
        assert player.in_jail is True


def test_move_and_resolve_draws_and_applies_cards(monkeypatch):
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    applied = []
    monkeypatch.setattr(
        game,
        "_apply_card",
        lambda p, card: applied.append((p, card)),
    )

    monkeypatch.setattr(
        player,
        "move",
        lambda steps: setattr(player, "position", 2) or 2,
    )
    game._move_and_resolve(player, 2)

    monkeypatch.setattr(
        player,
        "move",
        lambda steps: setattr(player, "position", 7) or 7,
    )
    game._move_and_resolve(player, 5)

    assert len(applied) == 2
    assert applied[0][0] == player
    assert applied[1][0] == player


def test_move_and_resolve_routes_property_like_tiles_to_property_handler(
    monkeypatch,
):
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    handled = []
    monkeypatch.setattr(
        game,
        "_handle_property_tile",
        lambda p, prop: handled.append((p, prop)),
    )

    monkeypatch.setattr(
        player,
        "move",
        lambda steps: setattr(player, "position", 1) or 1,
    )
    game._move_and_resolve(player, 1)

    assert handled and handled[0][0] == player


def test_railroad_tiles_have_property_objects():
    board = Board()

    for position in (5, 15, 25, 35):
        assert board.get_tile_type(position) == "railroad"
        assert board.get_property_at(position) is not None


def test_apply_card_branches(monkeypatch):
    game = Game(["Asha", "Ben", "Cara"])
    player = game.players[0]
    other_one = game.players[1]
    other_two = game.players[2]
    move_targets = []
    monkeypatch.setattr(
        game,
        "_handle_property_tile",
        lambda p, prop: move_targets.append((p, prop)),
    )

    collect_start = player.balance
    game._apply_card(player, {"description": "Collect", "action": "collect", "value": 50})
    assert player.balance == collect_start + 50

    pay_start = player.balance
    game._apply_card(player, {"description": "Pay", "action": "pay", "value": 20})
    assert player.balance == pay_start - 20

    game._apply_card(
        player,
        {"description": "Card", "action": "jail_free", "value": 0},
    )
    assert player.get_out_of_jail_cards == 1

    game._apply_card(player, {"description": "Jail", "action": "jail", "value": 0})
    assert player.in_jail is True

    player.in_jail = False
    player.position = 7
    boardwalk = game.board.get_property_at(39)
    game._apply_card(player, {"description": "Move", "action": "move_to", "value": 39})
    assert player.position == 39
    assert move_targets[-1] == (player, boardwalk)

    birthday_start = player.balance
    game._apply_card(
        player,
        {"description": "Birthday", "action": "birthday", "value": 10},
    )
    assert player.balance == birthday_start + 20
    assert other_one.balance == 1490
    assert other_two.balance == 1490

    collect_all_start = player.balance
    game._apply_card(
        player,
        {"description": "Collect all", "action": "collect_from_all", "value": 50},
    )
    assert player.balance == collect_all_start + 100
    assert other_one.balance == 1440
    assert other_two.balance == 1440


def test_apply_card_collect_from_all_skips_players_without_enough_money():
    game = Game(["Asha", "Ben", "Cara"])
    player = game.players[0]
    game.players[1].balance = 5
    game.players[2].balance = 60

    game._apply_card(
        player,
        {"description": "Collect all", "action": "collect_from_all", "value": 10},
    )

    assert player.balance == 1510
    assert game.players[1].balance == 5
    assert game.players[2].balance == 50


def test_check_bankruptcy_removes_player_and_resets_properties():
    game = Game(["Asha", "Ben"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    player.balance = 0

    game._check_bankruptcy(player)

    assert player.is_eliminated is True
    assert player not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False


def test_player_net_worth_includes_owned_property_values():
    player = Player("Asha")
    mortgaged = Property("Cheap Place", 1, 60, 2)
    premium = Property("Boardwalk", 39, 400, 50)
    player.add_property(mortgaged)
    player.add_property(premium)
    mortgaged.is_mortgaged = True

    assert player.net_worth() == 1500 + mortgaged.mortgage_value + premium.price


def test_find_winner_returns_richest_player():
    game = Game(["Asha", "Ben", "Cara"])
    game.players[0].balance = 1200
    game.players[1].balance = 1700
    game.players[2].balance = 1800
    prop = game.board.get_property_at(39)
    prop.owner = game.players[1]
    game.players[1].add_property(prop)

    winner = game.find_winner()

    assert winner == game.players[1]


def test_auction_property_rejects_owned_or_mortgaged_property():
    game = Game(["Asha", "Ben"])
    prop = game.board.get_property_at(1)
    prop.owner = game.players[0]

    assert game.auction_property(prop) is False

    prop.owner = None
    prop.is_mortgaged = True
    assert game.auction_property(prop) is False


def test_safe_int_input_returns_default_on_invalid_entry(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "not-a-number")
    assert ui.safe_int_input("Value: ", default=7) == 7


def test_play_turn_calls_interactive_menu_before_rolling(monkeypatch):
    game = Game(["Asha", "Ben"])
    menu_calls = []
    move_calls = []

    monkeypatch.setattr(
        game,
        "interactive_menu",
        lambda player: menu_calls.append(player.name),
    )
    monkeypatch.setattr(game.dice, "roll", lambda: 3)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 2 = 3")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    monkeypatch.setattr(
        game,
        "_move_and_resolve",
        lambda player, roll: move_calls.append((player.name, roll)),
    )

    game.play_turn()

    assert menu_calls == ["Asha"]
    assert move_calls == [("Asha", 3)]


def test_play_turn_bankruptcy_does_not_skip_next_player(monkeypatch):
    game = Game(["Asha", "Ben", "Cara"])
    current_player = game.players[0]

    monkeypatch.setattr(game, "interactive_menu", lambda player: None)
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)

    def bankrupt_current(player, roll):
        player.balance = 0
        game._check_bankruptcy(player)

    monkeypatch.setattr(game, "_move_and_resolve", bankrupt_current)

    game.play_turn()

    assert current_player not in game.players
    assert game.current_player().name == "Ben"
    assert game.turn_number == 1


def test_bankrupt_player_does_not_grant_extra_turn_after_doubles(monkeypatch):
    game = Game(["Asha", "Ben", "Cara"])
    current_player = game.players[0]

    monkeypatch.setattr(game, "interactive_menu", lambda player: None)
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4 (DOUBLES)")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
    game.dice.doubles_streak = 1

    def bankrupt_current(player, roll):
        player.balance = 0
        game._check_bankruptcy(player)

    monkeypatch.setattr(game, "_move_and_resolve", bankrupt_current)

    game.play_turn()

    assert current_player not in game.players
    assert game.current_player().name == "Ben"
    assert game.turn_number == 1
