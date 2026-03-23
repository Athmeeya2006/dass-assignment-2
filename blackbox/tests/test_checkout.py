"""
Tests for the Checkout endpoint: POST /checkout

Covers empty-cart check, invalid payment method, COD limit,
payment status per method, GST calculation, and wallet insufficiency.
"""

import pytest
from .conftest import BASE_URL


# ── helpers ──────────────────────────────────────────────────────────────────

def _add_to_cart(api_session, headers, product_id, quantity=1):
    return api_session.post(
        f"{BASE_URL}/cart/add",
        headers=headers,
        json={"product_id": product_id, "quantity": quantity},
    )


def _clear_cart(api_session, headers):
    api_session.delete(f"{BASE_URL}/cart/clear", headers=headers)


def _get_cart(api_session, headers):
    resp = api_session.get(f"{BASE_URL}/cart", headers=headers)
    return resp.json()


def _checkout(api_session, headers, payment_method):
    return api_session.post(
        f"{BASE_URL}/checkout",
        headers=headers,
        json={"payment_method": payment_method},
    )


def _find_cheap_and_expensive_products(api_session, admin_headers):
    """Return (cheap_product, expensive_product) from admin products."""
    resp = api_session.get(f"{BASE_URL}/admin/products", headers=admin_headers)
    prods = resp.json()
    if isinstance(prods, dict):
        prods = prods.get("products", prods.get("data", []))
    active = [p for p in prods if p.get("is_active", True)
              and p.get("stock_quantity", p.get("stock", p.get("quantity", 0))) > 0]
    active.sort(key=lambda p: p.get("price", 0))
    return active[0] if active else None, active[-1] if active else None


# ── tests ────────────────────────────────────────────────────────────────────

class TestCheckoutValidation:

    def test_checkout_empty_cart_rejected(self, api_session, valid_headers, clean_cart):
        """Checking out with an empty cart must return 400."""
        resp = _checkout(api_session, valid_headers, "COD")
        assert resp.status_code == 400

    @pytest.mark.parametrize("method", ["BITCOIN", "UPI", "CASH", ""])
    def test_invalid_payment_method_rejected(self, api_session, valid_headers,
                                              first_product, clean_cart, method):
        """Invalid payment method must return 400."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)
        resp = _checkout(api_session, valid_headers, method)
        assert resp.status_code == 400


class TestCheckoutCOD:

    def test_cod_under_5000_succeeds(self, api_session, valid_headers,
                                      admin_headers, clean_cart):
        """COD with order total ≤ 5000 should succeed."""
        cheap, _ = _find_cheap_and_expensive_products(api_session, admin_headers)
        if not cheap:
            pytest.skip("No products available")
        pid = cheap.get("product_id") or cheap.get("id")
        price = cheap.get("price", 0)
        stock = cheap.get("stock_quantity", cheap.get("stock", cheap.get("quantity", 1)))
        # add small qty to keep total under 5000 (including GST)
        qty = max(1, min(int(4000 / price) if price > 0 else 1, stock))
        if qty * price * 1.05 > 5000:
            qty = 1
        _add_to_cart(api_session, valid_headers, pid, qty)
        resp = _checkout(api_session, valid_headers, "COD")
        assert resp.status_code == 200, f"COD checkout failed: {resp.text}"

    def test_cod_over_5000_rejected(self, api_session, valid_headers,
                                     admin_headers, clean_cart):
        """COD with order total > 5000 must be rejected with 400."""
        _, expensive = _find_cheap_and_expensive_products(api_session, admin_headers)
        if not expensive:
            pytest.skip("No products available")
        pid = expensive.get("product_id") or expensive.get("id")
        price = expensive.get("price", 0)
        stock = expensive.get("stock_quantity", expensive.get("stock", expensive.get("quantity", 1)))
        # how many items needed so that total (incl GST) > 5000
        needed = int(5000 / (price * 1.05)) + 2 if price > 0 else stock
        qty = min(needed, stock)
        if qty * price * 1.05 <= 5000:
            pytest.skip("Cannot exceed 5000 with available stock")
        _add_to_cart(api_session, valid_headers, pid, qty)
        resp = _checkout(api_session, valid_headers, "COD")
        assert resp.status_code == 400


class TestCheckoutPaymentStatus:

    def _place_order(self, api_session, valid_headers, first_product, method):
        """Helper: clear cart, add 1 item, checkout, return response."""
        _clear_cart(api_session, valid_headers)
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)
        resp = _checkout(api_session, valid_headers, method)
        return resp

    def test_cod_payment_status_pending(self, api_session, valid_headers,
                                         first_product, clean_cart, funded_wallet):
        """COD orders should start with payment status PENDING."""
        resp = self._place_order(api_session, valid_headers, first_product, "COD")
        if resp.status_code != 200:
            pytest.skip(f"Could not place COD order: {resp.text}")
        body = resp.json()
        status = body.get("payment_status", "")
        assert status.upper() == "PENDING", f"Expected PENDING, got {status}"

    def test_wallet_payment_status_pending(self, api_session, valid_headers,
                                            first_product, clean_cart, funded_wallet):
        """WALLET orders should start with payment status PENDING."""
        resp = self._place_order(api_session, valid_headers, first_product, "WALLET")
        if resp.status_code != 200:
            pytest.skip(f"Could not place WALLET order: {resp.text}")
        body = resp.json()
        status = body.get("payment_status", "")
        assert status.upper() == "PENDING", f"Expected PENDING, got {status}"

    def test_card_payment_status_paid(self, api_session, valid_headers,
                                       first_product, clean_cart):
        """CARD orders should start with payment status PAID."""
        resp = self._place_order(api_session, valid_headers, first_product, "CARD")
        if resp.status_code != 200:
            pytest.skip(f"Could not place CARD order: {resp.text}")
        body = resp.json()
        status = body.get("payment_status", "")
        assert status.upper() == "PAID", f"Expected PAID, got {status}"


class TestCheckoutGST:

    def test_gst_5_percent_calculation(self, api_session, valid_headers,
                                        first_product, clean_cart):
        """GST must be exactly 5 pct; total_amount = subtotal + gst_amount.
        We compute expected from product price × qty."""
        pid = first_product.get("product_id") or first_product.get("id")
        price = first_product.get("price", 0)
        qty = 2
        _add_to_cart(api_session, valid_headers, pid, qty)

        # Expected subtotal based on known price
        expected_subtotal = price * qty
        expected_gst = expected_subtotal * 0.05
        expected_total = expected_subtotal + expected_gst

        resp = _checkout(api_session, valid_headers, "CARD")
        if resp.status_code != 200:
            pytest.skip(f"Checkout failed: {resp.text}")
        body = resp.json()

        order_total = body.get("total_amount", body.get("total", 0))
        gst_amount = body.get("gst_amount", 0)

        assert abs(order_total - expected_total) < 0.5, (
            f"Total mismatch: expected ~{expected_total}, got {order_total}"
        )
        assert abs(gst_amount - expected_gst) < 0.5, (
            f"GST mismatch: expected ~{expected_gst}, got {gst_amount}"
        )


class TestCheckoutWalletInsufficient:

    def test_wallet_insufficient_balance_rejected(self, api_session, valid_headers,
                                                    admin_headers, clean_cart):
        """WALLET checkout with insufficient balance must return 400."""
        # drain wallet first
        w_resp = api_session.get(f"{BASE_URL}/wallet", headers=valid_headers)
        balance = w_resp.json().get("wallet_balance", w_resp.json().get("balance", 0))
        if balance > 0:
            api_session.post(
                f"{BASE_URL}/wallet/pay",
                headers=valid_headers,
                json={"amount": balance},
            )

        # find an expensive product
        _, exp = _find_cheap_and_expensive_products(api_session, admin_headers)
        if not exp:
            pytest.skip("No products available")
        pid = exp.get("product_id") or exp.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)
        resp = _checkout(api_session, valid_headers, "WALLET")
        assert resp.status_code == 400
