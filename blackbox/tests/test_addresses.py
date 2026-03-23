"""
Tests for the Addresses endpoints:
  GET /addresses, POST /addresses, PUT /addresses/{id}, DELETE /addresses/{id}

Covers label validation, field length constraints, pincode format,
default-address exclusivity, immutable fields on update, and deletion.
"""

import pytest
from .conftest import BASE_URL


# ── helpers ──────────────────────────────────────────────────────────────────

def _base_address():
    """Return a valid address payload."""
    return {
        "label": "HOME",
        "street": "123 Main Street Valid",
        "city": "TestCity",
        "pincode": "123456",
        "is_default": False,
    }


def _extract_address(body):
    """Handle both {"address": {...}} and flat {...} response shapes."""
    if isinstance(body, dict) and "address" in body:
        return body["address"]
    return body


def _get_address_id(body):
    """Extract address_id from creation response."""
    addr = _extract_address(body)
    return addr.get("address_id") or addr.get("id")


def _get_all_addresses(api_session, headers):
    """GET /addresses and return the list."""
    resp = api_session.get(f"{BASE_URL}/addresses", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("addresses", body.get("data", []))


def _find_address(addresses, addr_id):
    """Find an address by ID in a list."""
    for a in addresses:
        aid = a.get("address_id") or a.get("id")
        if str(aid) == str(addr_id):
            return a
    return None


# ── creation validation ──────────────────────────────────────────────────────

class TestAddressCreation:

    def test_post_valid_home_address(self, api_session, valid_headers):
        """POST valid address with label HOME must succeed and return address_id."""
        resp = api_session.post(
            f"{BASE_URL}/addresses", headers=valid_headers, json=_base_address()
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        addr = _extract_address(body)
        assert ("address_id" in addr) or ("id" in addr), "Response missing address identifier"

    @pytest.mark.parametrize("bad_label", ["WORKSPACE", "CABIN", "HOME_2"])
    def test_invalid_label_rejected(self, api_session, valid_headers, bad_label):
        """Label not in [HOME, OFFICE, OTHER] must be rejected with 400."""
        payload = _base_address()
        payload["label"] = bad_label
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad_street", ["abcd", "a" * 101])
    def test_invalid_street_length_rejected(self, api_session, valid_headers, bad_street):
        """Street outside 5-100 chars must be rejected with 400."""
        payload = _base_address()
        payload["street"] = bad_street
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad_city", ["A", "A" * 51])
    def test_invalid_city_length_rejected(self, api_session, valid_headers, bad_city):
        """City outside 2-50 chars must be rejected with 400."""
        payload = _base_address()
        payload["city"] = bad_city
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad_pin", ["12345", "1234567"])
    def test_invalid_pincode_rejected(self, api_session, valid_headers, bad_pin):
        """Pincode not exactly 6 digits must be rejected with 400."""
        payload = _base_address()
        payload["pincode"] = bad_pin
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad_pin", ["abcdef"])
    def test_invalid_pincode_letters_rejected(self, api_session, valid_headers, bad_pin):
        """Pincode with letters must be rejected with 400.
        BUG: Server accepts letters in pincode."""
        payload = _base_address()
        payload["pincode"] = bad_pin
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code == 400, "BUG: Server accepted letters in pincode"
        
    @pytest.mark.parametrize("pin", ["000000"])
    def test_valid_pincode_zeroes_succeeds(self, api_session, valid_headers, pin):
        """Pincode of 6 zeroes must succeed."""
        payload = _base_address()
        payload["pincode"] = pin
        resp = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=payload)
        assert resp.status_code in (200, 201)


# ── default address logic ────────────────────────────────────────────────────

class TestAddressDefault:

    def test_only_one_default_at_a_time(self, api_session, valid_headers):
        """Adding two default addresses: only the latest must be default."""
        p1 = _base_address()
        p1["is_default"] = True
        resp1 = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=p1)
        assert resp1.status_code in (200, 201)
        id1 = _get_address_id(resp1.json())

        p2 = _base_address()
        p2["label"] = "OFFICE"
        p2["is_default"] = True
        resp2 = api_session.post(f"{BASE_URL}/addresses", headers=valid_headers, json=p2)
        assert resp2.status_code in (200, 201)
        id2 = _get_address_id(resp2.json())

        all_addrs = _get_all_addresses(api_session, valid_headers)
        addr1 = _find_address(all_addrs, id1)
        addr2 = _find_address(all_addrs, id2)

        if addr1:
            assert addr1.get("is_default") is False, "First address should no longer be default"
        if addr2:
            assert addr2.get("is_default") is True, "Second address should be the new default"


# ── update ───────────────────────────────────────────────────────────────────

class TestAddressUpdate:

    def _create(self, api_session, headers):
        """Create and return an address id."""
        resp = api_session.post(f"{BASE_URL}/addresses", headers=headers, json=_base_address())
        assert resp.status_code in (200, 201)
        return _get_address_id(resp.json())

    def test_change_street_reflected(self, api_session, valid_headers):
        """PUT with new street must be reflected in subsequent GET."""
        aid = self._create(api_session, valid_headers)
        new_street = "789 Updated Boulevard"
        resp = api_session.put(
            f"{BASE_URL}/addresses/{aid}", headers=valid_headers,
            json={"street": new_street},
        )
        assert resp.status_code in (200, 204)

        all_addrs = _get_all_addresses(api_session, valid_headers)
        addr = _find_address(all_addrs, aid)
        assert addr is not None, "Address not found after update"
        assert addr.get("street") == new_street

    def test_city_not_changeable(self, api_session, valid_headers):
        """PUT attempting to change city must leave city unchanged."""
        aid = self._create(api_session, valid_headers)
        api_session.put(
            f"{BASE_URL}/addresses/{aid}", headers=valid_headers,
            json={"city": "HackedCity"},
        )
        all_addrs = _get_all_addresses(api_session, valid_headers)
        addr = _find_address(all_addrs, aid)
        assert addr is not None
        assert addr.get("city") == "TestCity"

    def test_label_not_changeable(self, api_session, valid_headers):
        """PUT attempting to change label must leave label unchanged."""
        aid = self._create(api_session, valid_headers)
        api_session.put(
            f"{BASE_URL}/addresses/{aid}", headers=valid_headers,
            json={"label": "OFFICE"},
        )
        all_addrs = _get_all_addresses(api_session, valid_headers)
        addr = _find_address(all_addrs, aid)
        assert addr is not None
        assert addr.get("label") == "HOME"

    def test_pincode_not_changeable(self, api_session, valid_headers):
        """PUT attempting to change pincode must leave pincode unchanged."""
        aid = self._create(api_session, valid_headers)
        api_session.put(
            f"{BASE_URL}/addresses/{aid}", headers=valid_headers,
            json={"pincode": "999999"},
        )
        all_addrs = _get_all_addresses(api_session, valid_headers)
        addr = _find_address(all_addrs, aid)
        assert addr is not None
        assert addr.get("pincode") == "123456"


# ── delete ───────────────────────────────────────────────────────────────────

class TestAddressDelete:

    def test_delete_existing_success(self, api_session, valid_headers):
        """DELETE existing address must succeed."""
        resp = api_session.post(
            f"{BASE_URL}/addresses", headers=valid_headers, json=_base_address()
        )
        aid = _get_address_id(resp.json())
        del_resp = api_session.delete(f"{BASE_URL}/addresses/{aid}", headers=valid_headers)
        assert del_resp.status_code in (200, 204)

    def test_delete_nonexistent_returns_404(self, api_session, valid_headers):
        """DELETE non-existent address must return 404."""
        resp = api_session.delete(f"{BASE_URL}/addresses/999999999", headers=valid_headers)
        assert resp.status_code == 404


# ── list ─────────────────────────────────────────────────────────────────────

class TestAddressList:

    def test_get_returns_list(self, api_session, valid_headers):
        """GET /addresses must return data in a list format."""
        resp = api_session.get(f"{BASE_URL}/addresses", headers=valid_headers)
        assert resp.status_code == 200
        body = resp.json()
        is_list = isinstance(body, list)
        is_wrapped = isinstance(body, dict) and (
            isinstance(body.get("addresses"), list) or isinstance(body.get("data"), list)
        )
        assert is_list or is_wrapped, "Response is not a list or list-wrapped dict"
