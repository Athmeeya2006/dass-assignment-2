"""
Tests for the Wallet endpoints:
  GET /wallet, POST /wallet/add, POST /wallet/pay

Covers balance retrieval, add-money boundaries,
pay validation, and exact deduction.

NOTE: Test documents a known wallet pay deduction bug.
"""

import pytest
from .conftest import BASE_URL


def _get_balance(api_session, headers):
    resp = api_session.get(f"{BASE_URL}/wallet", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    return body.get("wallet_balance", body.get("balance", 0))


class TestWalletGet:

    def test_get_wallet_returns_balance(self, api_session, valid_headers):
        """GET /wallet must return a wallet_balance field."""
        resp = api_session.get(f"{BASE_URL}/wallet", headers=valid_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "wallet_balance" in body or "balance" in body, (
            "Response missing balance field"
        )


class TestWalletAdd:

    @pytest.mark.parametrize("amount", [0, -1, -100])
    def test_add_zero_or_negative_rejected(self, api_session, valid_headers, amount):
        """Adding ≤ 0 must be rejected with 400."""
        resp = api_session.post(
            f"{BASE_URL}/wallet/add",
            headers=valid_headers,
            json={"amount": amount},
        )
        assert resp.status_code == 400

    def test_add_1_succeeds(self, api_session, valid_headers):
        """Adding amount=1 should succeed."""
        resp = api_session.post(
            f"{BASE_URL}/wallet/add",
            headers=valid_headers,
            json={"amount": 1},
        )
        assert resp.status_code == 200

    def test_add_100000_succeeds(self, api_session, valid_headers):
        """Boundary: adding exactly 100 000 should succeed."""
        resp = api_session.post(
            f"{BASE_URL}/wallet/add",
            headers=valid_headers,
            json={"amount": 100000},
        )
        assert resp.status_code == 200

    def test_add_100001_rejected(self, api_session, valid_headers):
        """Boundary: adding 100 001 (above max) must be rejected."""
        resp = api_session.post(
            f"{BASE_URL}/wallet/add",
            headers=valid_headers,
            json={"amount": 100001},
        )
        assert resp.status_code == 400


class TestWalletPay:

    @pytest.mark.parametrize("amount", [0, -1])
    def test_pay_zero_or_negative_rejected(self, api_session, valid_headers, amount):
        """Paying ≤ 0 must be rejected with 400."""
        resp = api_session.post(
            f"{BASE_URL}/wallet/pay",
            headers=valid_headers,
            json={"amount": amount},
        )
        assert resp.status_code == 400

    def test_pay_more_than_balance_rejected(self, api_session, valid_headers):
        """Paying more than current balance must return 400."""
        balance = _get_balance(api_session, valid_headers)
        resp = api_session.post(
            f"{BASE_URL}/wallet/pay",
            headers=valid_headers,
            json={"amount": balance + 1000},
        )
        assert resp.status_code == 400

    def test_pay_deducts_exact_amount(self, api_session, valid_headers):
        """After paying X, balance must decrease by exactly X.
        BUG: Server deducts slightly incorrect amount (off by ~0.2)."""
        # ensure enough funds — add a clean 1000
        api_session.post(
            f"{BASE_URL}/wallet/add",
            headers=valid_headers,
            json={"amount": 1000},
        )
        before = _get_balance(api_session, valid_headers)
        pay_amount = 200

        resp = api_session.post(
            f"{BASE_URL}/wallet/pay",
            headers=valid_headers,
            json={"amount": pay_amount},
        )
        assert resp.status_code == 200

        after = _get_balance(api_session, valid_headers)
        expected = before - pay_amount
        assert abs(after - expected) < 0.01, (
            f"BUG: Balance mismatch: expected {expected}, got {after} "
            f"(off by {abs(after - expected)})"
        )
