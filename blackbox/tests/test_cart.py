"""
Tests for the Cart endpoints:
  GET /cart, POST /cart/add, POST /cart/update,
  POST /cart/remove, DELETE /cart/clear

Covers quantity validation, stock limits, additive quantity logic,
subtotal/total calculations, and removal edge cases.

NOTE: Several tests document known API bugs:
  - Cart accepts quantity=0 and negative quantities (BUG)
  - Cart subtotal ≠ quantity × unit_price (BUG)
  - Cart total is always 0 instead of sum of subtotals (BUG)
"""

import pytest
from .conftest import BASE_URL


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_cart(api_session, headers):
    """Return the cart body dict."""
    resp = api_session.get(f"{BASE_URL}/cart", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def _cart_items(body):
    """Extract the items list from a cart response."""
    if isinstance(body, list):
        return body
    return body.get("items", body.get("cart", body.get("data", [])))


def _add_to_cart(api_session, headers, product_id, quantity=1):
    return api_session.post(
        f"{BASE_URL}/cart/add",
        headers=headers,
        json={"product_id": product_id, "quantity": quantity},
    )


# ── quantity validation ──────────────────────────────────────────────────────

class TestCartAddValidation:

    @pytest.mark.parametrize("qty", [0, -1, -100])
    def test_add_invalid_quantity_rejected(self, api_session, valid_headers,
                                           first_product, clean_cart, qty):
        """Quantity ≤ 0 must be rejected with 400 per docs.
        BUG: Server accepts these quantities instead of rejecting."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _add_to_cart(api_session, valid_headers, pid, qty)
        # KNOWN BUG: server returns 200, docs say 400
        assert resp.status_code == 400, (
            f"BUG: Server accepted quantity={qty} (status {resp.status_code}), "
            f"docs require 400 rejection"
        )

    def test_add_quantity_1_succeeds(self, api_session, valid_headers,
                                     first_product, clean_cart):
        """Adding quantity=1 of an existing product must succeed."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _add_to_cart(api_session, valid_headers, pid, 1)
        assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"

    def test_add_nonexistent_product_returns_404(self, api_session, valid_headers,
                                                  clean_cart):
        """Adding a product that does not exist must return 404."""
        resp = _add_to_cart(api_session, valid_headers, 999999, 1)
        assert resp.status_code == 404

    def test_add_exceeding_stock_returns_400(self, api_session, valid_headers,
                                              first_product, clean_cart,
                                              admin_headers):
        """Requesting more than available stock must be rejected."""
        pid = first_product.get("product_id") or first_product.get("id")
        # get stock from admin
        admin_resp = api_session.get(f"{BASE_URL}/admin/products", headers=admin_headers)
        admin_all = admin_resp.json()
        if isinstance(admin_all, dict):
            admin_all = admin_all.get("products", admin_all.get("data", []))
        prod = next((p for p in admin_all if (p.get("product_id") or p.get("id")) == pid), None)
        stock = prod.get("stock", prod.get("stock_quantity", prod.get("quantity", 9999)))
        resp = _add_to_cart(api_session, valid_headers, pid, stock + 1)
        assert resp.status_code == 400


# ── additive quantity logic ──────────────────────────────────────────────────

class TestCartAdditiveQuantity:

    def test_same_product_quantities_add(self, api_session, valid_headers,
                                          first_product, clean_cart):
        """Adding the same product twice sums quantities (2+3=5)."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 2)
        _add_to_cart(api_session, valid_headers, pid, 3)

        cart = _get_cart(api_session, valid_headers)
        items = _cart_items(cart)
        item = next(
            (i for i in items if (i.get("product_id") or i.get("id")) == pid),
            None,
        )
        assert item is not None, "Product not found in cart"
        assert item["quantity"] == 5, f"Expected qty=5, got {item['quantity']}"


# ── subtotal & total math ───────────────────────────────────────────────────

class TestCartMath:

    def test_item_subtotal_is_qty_times_price(self, api_session, valid_headers,
                                               first_product, clean_cart):
        """Each item subtotal must equal quantity × unit_price.
        BUG: Server returns incorrect subtotal (not qty × price)."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 3)

        cart = _get_cart(api_session, valid_headers)
        items = _cart_items(cart)
        item = next(
            (i for i in items if (i.get("product_id") or i.get("id")) == pid),
            None,
        )
        assert item is not None
        expected_subtotal = item["quantity"] * item.get("unit_price", item.get("price", 0))
        actual_subtotal = item.get("subtotal", item.get("item_total", 0))
        assert abs(actual_subtotal - expected_subtotal) < 0.01, (
            f"BUG: Subtotal mismatch: expected {expected_subtotal} "
            f"(qty={item['quantity']} × price={item.get('unit_price', item.get('price'))}), "
            f"got {actual_subtotal}"
        )

    def test_cart_total_is_sum_of_subtotals(self, api_session, valid_headers,
                                             all_products, clean_cart):
        """Cart total must equal sum of all item subtotals.
        BUG: Server returns total=0 regardless of items."""
        # add two different products
        for p in all_products[:2]:
            pid = p.get("product_id") or p.get("id")
            _add_to_cart(api_session, valid_headers, pid, 1)

        cart = _get_cart(api_session, valid_headers)
        items = _cart_items(cart)

        # Compute expected total from unit_price × quantity
        computed_total = sum(
            i.get("quantity", 0) * i.get("unit_price", i.get("price", 0))
            for i in items
        )
        cart_total = cart.get("total", cart.get("cart_total", 0))
        assert abs(cart_total - computed_total) < 0.01, (
            f"BUG: Cart total={cart_total}, expected={computed_total} "
            f"(sum of qty × unit_price for all items)"
        )


# ── update ───────────────────────────────────────────────────────────────────

class TestCartUpdate:

    @pytest.mark.parametrize("qty", [0, -1, -50])
    def test_update_invalid_quantity_rejected(self, api_session, valid_headers,
                                              first_product, clean_cart, qty):
        """Updating cart item quantity to ≤ 0 must be rejected.
        BUG: Server accepts these quantities instead of rejecting."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)
        resp = api_session.post(
            f"{BASE_URL}/cart/update",
            headers=valid_headers,
            json={"product_id": pid, "quantity": qty},
        )
        assert resp.status_code == 400, (
            f"BUG: Server accepted cart update to quantity={qty} (status {resp.status_code})"
        )

    def test_update_quantity_1_succeeds(self, api_session, valid_headers,
                                        first_product, clean_cart):
        """Updating to quantity=1 must succeed."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 2)
        resp = api_session.post(
            f"{BASE_URL}/cart/update",
            headers=valid_headers,
            json={"product_id": pid, "quantity": 1},
        )
        assert resp.status_code == 200


# ── remove ───────────────────────────────────────────────────────────────────

class TestCartRemove:

    def test_remove_item_not_in_cart_returns_404(self, api_session, valid_headers,
                                                  clean_cart):
        """Removing a product that is not in the cart must return 404.
        BUG: Server returns 200 even if product is not in cart."""
        resp = api_session.post(
            f"{BASE_URL}/cart/remove",
            headers=valid_headers,
            json={"product_id": 999999},
        )
        assert resp.status_code == 404, (
            f"BUG: Server returned {resp.status_code} when removing non-existent cart item"
        )


# ── clear ────────────────────────────────────────────────────────────────────

class TestCartClear:

    def test_clear_empties_cart(self, api_session, valid_headers, first_product):
        """DELETE /cart/clear should result in an empty cart."""
        pid = first_product.get("product_id") or first_product.get("id")
        _add_to_cart(api_session, valid_headers, pid, 1)
        resp = api_session.delete(f"{BASE_URL}/cart/clear", headers=valid_headers)
        assert resp.status_code == 200

        cart = _get_cart(api_session, valid_headers)
        items = _cart_items(cart)
        assert len(items) == 0, "Cart should be empty after clear"
