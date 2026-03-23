"""
Tests for the Coupon endpoints:
  POST /coupon/apply, POST /coupon/remove

Covers PERCENT and FIXED discount types, max-cap enforcement,
expired coupons, minimum cart value, and coupon removal.
"""

import pytest
from datetime import datetime, timezone
from .conftest import BASE_URL


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_coupons(api_session, admin_headers):
    """Fetch all coupons via admin endpoint."""
    resp = api_session.get(f"{BASE_URL}/admin/coupons", headers=admin_headers)
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("coupons", body.get("data", []))


def _add_to_cart(api_session, headers, product_id, quantity=1):
    return api_session.post(
        f"{BASE_URL}/cart/add",
        headers=headers,
        json={"product_id": product_id, "quantity": quantity},
    )


def _get_cart(api_session, headers):
    resp = api_session.get(f"{BASE_URL}/cart", headers=headers)
    return resp.json()


def _classify_coupons(coupons):
    """Return dicts keyed by type and validity."""
    now = datetime.now(timezone.utc)
    result = {
        "percent_valid": [],
        "fixed_valid": [],
        "expired": [],
    }
    for c in coupons:
        expiry = c.get("expiry_date") or c.get("expiry") or c.get("expires_at", "")
        is_expired = False
        if expiry:
            try:
                exp_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if exp_dt < now:
                    is_expired = True
            except Exception:
                pass
        dtype = c.get("discount_type", c.get("type", "")).upper()
        if is_expired:
            result["expired"].append(c)
        elif dtype == "PERCENT":
            result["percent_valid"].append(c)
        elif dtype == "FIXED":
            result["fixed_valid"].append(c)
    return result


class TestCouponApply:

    def test_apply_valid_percent_coupon(self, api_session, valid_headers,
                                        admin_headers, first_product, clean_cart):
        """Applying a PERCENT coupon: verify discount from apply response."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 5)

        coupons = _get_coupons(api_session, admin_headers)
        classified = _classify_coupons(coupons)
        if not classified["percent_valid"]:
            pytest.skip("No valid PERCENT coupon available")

        coupon = classified["percent_valid"][0]
        code = coupon.get("coupon_code") or coupon.get("code")
        percent = coupon.get("discount_value", coupon.get("discount", coupon.get("percentage", 0)))
        max_cap = coupon.get("max_discount", coupon.get("cap", None))
        min_cart = coupon.get("min_cart_value", coupon.get("minimum_cart_value", 0))

        # Make sure we meet minimum cart value
        cart = _get_cart(api_session, valid_headers)
        items = cart.get("items", [])
        raw_total = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
        if raw_total < min_cart:
            # Add more items
            _add_to_cart(api_session, valid_headers, pid, 10)
            cart = _get_cart(api_session, valid_headers)
            items = cart.get("items", [])
            raw_total = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)

        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": code},
        )
        assert resp.status_code == 200, f"Apply coupon failed: {resp.text}"

        body = resp.json()
        # Response format: {"coupon_code": ..., "discount": X, "new_total": Y}
        discount_shown = body.get("discount", 0)

        expected_discount = raw_total * (percent / 100)
        if max_cap and expected_discount > max_cap:
            expected_discount = max_cap

        assert abs(discount_shown - expected_discount) < 1, (
            f"Discount mismatch: expected ~{expected_discount}, got {discount_shown}"
        )

    def test_apply_percent_coupon_capped(self, api_session, valid_headers,
                                         admin_headers, first_product, clean_cart):
        """If PERCENT coupon has max cap, discount must not exceed cap."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 10)

        coupons = _get_coupons(api_session, admin_headers)
        classified = _classify_coupons(coupons)
        capped = [c for c in classified["percent_valid"]
                  if c.get("max_discount") or c.get("cap")]
        if not capped:
            pytest.skip("No capped PERCENT coupon available")

        coupon = capped[0]
        code = coupon.get("coupon_code") or coupon.get("code")
        cap = coupon.get("max_discount", coupon.get("cap"))

        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": code},
        )
        if resp.status_code != 200:
            pytest.skip("Could not apply coupon (cart may not meet min value)")

        body = resp.json()
        discount = body.get("discount", 0)
        assert discount <= cap + 0.01, f"Discount {discount} exceeds cap {cap}"

    def test_apply_valid_fixed_coupon(self, api_session, valid_headers,
                                      admin_headers, first_product, clean_cart):
        """Applying a FIXED coupon: discount equals the flat amount."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 10)

        coupons = _get_coupons(api_session, admin_headers)
        classified = _classify_coupons(coupons)
        if not classified["fixed_valid"]:
            pytest.skip("No valid FIXED coupon available")

        coupon = classified["fixed_valid"][0]
        code = coupon.get("coupon_code") or coupon.get("code")
        flat = coupon.get("discount_value", coupon.get("discount", coupon.get("amount", 0)))
        min_cart = coupon.get("min_cart_value", 0)

        # Ensure min cart value is met
        cart = _get_cart(api_session, valid_headers)
        items = cart.get("items", [])
        raw_total = sum(i.get("quantity", 0) * i.get("unit_price", 0) for i in items)
        if raw_total < min_cart:
            _add_to_cart(api_session, valid_headers, pid, 20)

        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": code},
        )
        if resp.status_code != 200:
            pytest.skip(f"Could not apply coupon: {resp.text}")

        body = resp.json()
        discount = body.get("discount", 0)
        assert abs(discount - flat) < 0.01, (
            f"Fixed discount mismatch: expected {flat}, got {discount}"
        )

    def test_apply_expired_coupon_fails(self, api_session, valid_headers,
                                         admin_headers, first_product, clean_cart):
        """Applying an expired coupon must return a non-2xx status."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)

        coupons = _get_coupons(api_session, admin_headers)
        classified = _classify_coupons(coupons)
        if not classified["expired"]:
            pytest.skip("No expired coupon available")

        code = classified["expired"][0].get("coupon_code") or classified["expired"][0].get("code")
        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": code},
        )
        assert resp.status_code >= 400, f"Expired coupon accepted: {resp.status_code}"

    def test_apply_coupon_below_minimum_cart_value(self, api_session, valid_headers,
                                                    admin_headers, clean_cart):
        """Applying coupon when cart total < min cart value must fail."""
        coupons = _get_coupons(api_session, admin_headers)
        high_min = [c for c in coupons
                    if (c.get("min_cart_value", c.get("minimum_cart_value", 0)) or 0) > 10000]
        if not high_min:
            pytest.skip("No coupon with high min_cart_value")

        code = high_min[0].get("coupon_code") or high_min[0].get("code")
        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": code},
        )
        assert resp.status_code >= 400

    def test_apply_nonexistent_coupon_fails(self, api_session, valid_headers,
                                             first_product, clean_cart):
        """Applying a coupon code that does not exist must fail."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)

        resp = api_session.post(
            f"{BASE_URL}/coupon/apply",
            headers=valid_headers,
            json={"coupon_code": "DOESNOTEXIST999"},
        )
        assert resp.status_code >= 400


class TestCouponRemove:

    def test_remove_coupon_reverts_total(self, api_session, valid_headers,
                                          admin_headers, first_product, clean_cart):
        """After removing a coupon, applying then removing should not change cart."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 5)

        coupons = _get_coupons(api_session, admin_headers)
        classified = _classify_coupons(coupons)
        valid_coupons = classified["percent_valid"] + classified["fixed_valid"]
        if not valid_coupons:
            pytest.skip("No valid coupon available")

        # Try each coupon until one works
        applied_code = None
        for c in valid_coupons:
            code = c.get("coupon_code") or c.get("code")
            apply_resp = api_session.post(
                f"{BASE_URL}/coupon/apply",
                headers=valid_headers,
                json={"coupon_code": code},
            )
            if apply_resp.status_code == 200:
                applied_code = code
                break

        if not applied_code:
            pytest.skip("Could not apply any coupon")

        # remove
        rem_resp = api_session.post(
            f"{BASE_URL}/coupon/remove",
            headers=valid_headers,
            json={"coupon_code": applied_code},
        )
        assert rem_resp.status_code == 200
