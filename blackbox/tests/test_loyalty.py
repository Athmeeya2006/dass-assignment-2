"""
Tests for the Loyalty endpoints:
  GET /loyalty, POST /loyalty/redeem

Covers points retrieval, invalid redemption amounts,
and successful redemption.
"""

import pytest
from .conftest import BASE_URL


def _get_points(api_session, headers):
    resp = api_session.get(f"{BASE_URL}/loyalty", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    return body.get("points", body.get("loyalty_points", 0))


class TestLoyaltyGet:

    def test_get_loyalty_returns_points(self, api_session, valid_headers):
        """GET /loyalty must contain a points field."""
        resp = api_session.get(f"{BASE_URL}/loyalty", headers=valid_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "points" in body or "loyalty_points" in body, (
            "Response missing points field"
        )


class TestLoyaltyRedeem:

    @pytest.mark.parametrize("amount", [0, -1])
    def test_redeem_zero_or_negative_rejected(self, api_session, valid_headers, amount):
        """Redeeming ≤ 0 points must be rejected with 400."""
        resp = api_session.post(
            f"{BASE_URL}/loyalty/redeem",
            headers=valid_headers,
            json={"points": amount},
        )
        assert resp.status_code == 400

    def test_redeem_more_than_available_rejected(self, api_session, valid_headers):
        """Redeeming more points than available must return an error."""
        current = _get_points(api_session, valid_headers)
        resp = api_session.post(
            f"{BASE_URL}/loyalty/redeem",
            headers=valid_headers,
            json={"points": current + 1000},
        )
        assert resp.status_code >= 400

    def test_redeem_valid_amount_succeeds(self, api_session, valid_headers):
        """Redeeming a valid number of points must succeed and reduce balance."""
        current = _get_points(api_session, valid_headers)
        if current < 1:
            pytest.skip("User has no loyalty points to redeem")

        redeem = min(current, 1)
        resp = api_session.post(
            f"{BASE_URL}/loyalty/redeem",
            headers=valid_headers,
            json={"points": redeem},
        )
        assert resp.status_code == 200

        after = _get_points(api_session, valid_headers)
        expected = current - redeem
        assert after == expected, (
            f"Points mismatch: expected {expected}, got {after}"
        )
