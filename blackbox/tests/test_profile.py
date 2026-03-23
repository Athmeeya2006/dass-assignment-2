"""
Tests for the Profile endpoints: GET /profile, PUT /profile

Covers fetching profile fields, name length validation (2-50),
phone format validation (exactly 10 digits), and round-trip updates.
"""

import pytest
from .conftest import BASE_URL


class TestProfileGet:

    def test_get_profile_returns_name_and_phone(self, api_session, valid_headers):
        """GET /profile must return a response containing name and phone fields."""
        resp = api_session.get(f"{BASE_URL}/profile", headers=valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data, "Profile response missing 'name'"
        assert "phone" in data, "Profile response missing 'phone'"


class TestProfileUpdateName:

    def test_put_valid_name_succeeds(self, api_session, valid_headers):
        """Updating profile with a valid name (2-50 chars) must succeed."""
        payload = {"name": "Valid Name", "phone": "1234567890"}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 200

    @pytest.mark.parametrize("bad_name", ["a", "X" * 51])
    def test_put_invalid_name_length_rejected(self, api_session, valid_headers, bad_name):
        """Name shorter than 2 or longer than 50 chars must be rejected with 400."""
        payload = {"name": bad_name, "phone": "1234567890"}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 400


class TestProfileUpdatePhone:

    @pytest.mark.parametrize("bad_phone", ["123456789", "12345678901", "12345abcde", "abcdefghij"])
    def test_put_invalid_phone_rejected(self, api_session, valid_headers, bad_phone):
        """Phone not exactly 10 digits or containing letters must be rejected with 400."""
        payload = {"name": "Test User", "phone": bad_phone}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 400

    def test_put_valid_10_digit_phone_succeeds(self, api_session, valid_headers):
        """Phone with exactly 10 digits must be accepted."""
        payload = {"name": "Phone Test", "phone": "9876543210"}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 200

    def test_put_empty_body_rejected(self, api_session, valid_headers):
        """Empty body must be rejected."""
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json={})
        assert resp.status_code == 400

    def test_put_name_exactly_2_chars_succeeds(self, api_session, valid_headers):
        """Name of exactly 2 characters must be accepted."""
        payload = {"name": "AB", "phone": "1234567890"}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 200

    def test_put_phone_all_zeroes_accepted(self, api_session, valid_headers):
        """Phone with 10 zeroes must be accepted."""
        payload = {"name": "Test User", "phone": "0000000000"}
        resp = api_session.put(f"{BASE_URL}/profile", headers=valid_headers, json=payload)
        assert resp.status_code == 200


class TestProfileRoundTrip:

    def test_get_returns_updated_values(self, api_session, valid_headers):
        """After PUT, GET must return the new name and phone."""
        new_name = "RoundTrip User"
        new_phone = "5555555555"
        api_session.put(
            f"{BASE_URL}/profile", headers=valid_headers,
            json={"name": new_name, "phone": new_phone},
        )
        resp = api_session.get(f"{BASE_URL}/profile", headers=valid_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("name") == new_name
        assert data.get("phone") == new_phone
