"""
Tests for authentication header validation.

Every API request requires X-Roll-Number. User-scoped endpoints also
require X-User-ID. This file verifies the server rejects invalid or
missing header combinations with the correct status codes.
"""

import pytest
from .conftest import BASE_URL, ROLL_NUMBER


class TestAuthRollNumber:

    def test_missing_roll_number_returns_401(self, api_session, setup_user):
        """Requests without X-Roll-Number must be rejected with 401."""
        headers = {"Content-Type": "application/json", "X-User-ID": setup_user["user_id"]}
        resp = api_session.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 401

    @pytest.mark.parametrize("bad_roll", ["abc", "!@#", "12.5"])
    def test_invalid_roll_number_returns_400(self, api_session, setup_user, bad_roll):
        """X-Roll-Number that is not a valid integer must be rejected with 400."""
        headers = {
            "X-Roll-Number": bad_roll,
            "X-User-ID": setup_user["user_id"],
            "Content-Type": "application/json",
        }
        resp = api_session.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400


class TestAuthUserId:

    def test_missing_user_id_returns_400(self, api_session):
        """User-scoped endpoint without X-User-ID must return 400."""
        headers = {"X-Roll-Number": ROLL_NUMBER, "Content-Type": "application/json"}
        resp = api_session.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad_uid", ["abc", "1.5", ""])
    def test_non_integer_user_id_returns_400(self, api_session, bad_uid):
        """X-User-ID that is not a valid integer must return 400."""
        headers = {
            "X-Roll-Number": ROLL_NUMBER,
            "X-User-ID": bad_uid,
            "Content-Type": "application/json",
        }
        resp = api_session.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    def test_nonexistent_user_id_returns_400(self, api_session):
        """X-User-ID referencing a user that does not exist must return 400."""
        headers = {
            "X-Roll-Number": ROLL_NUMBER,
            "X-User-ID": "999999999",
            "Content-Type": "application/json",
        }
        resp = api_session.get(f"{BASE_URL}/profile", headers=headers)
        assert resp.status_code == 400

    def test_valid_headers_succeed(self, api_session, valid_headers):
        """Both headers valid → request must succeed with 200."""
        resp = api_session.get(f"{BASE_URL}/profile", headers=valid_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)
