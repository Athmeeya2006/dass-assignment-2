"""
Tests for the Orders endpoints:
  GET /orders, GET /orders/{id}, POST /orders/{id}/cancel,
  GET /orders/{id}/invoice

Covers listing, detail, cancellation rules, stock restoration,
and invoice math (subtotal / GST / total).
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


def _checkout(api_session, headers, method="CARD"):
    return api_session.post(
        f"{BASE_URL}/checkout",
        headers=headers,
        json={"payment_method": method},
    )


def _place_order(api_session, headers, product_id, qty=1, method="CARD"):
    """Clear cart, add item, checkout, return (resp, order_body)."""
    _clear_cart(api_session, headers)
    _add_to_cart(api_session, headers, product_id, qty)
    resp = _checkout(api_session, headers, method)
    body = resp.json() if resp.content else {}
    return resp, body


def _get_order(api_session, headers, order_id):
    resp = api_session.get(f"{BASE_URL}/orders/{order_id}", headers=headers)
    return resp


def _get_stock(api_session, admin_headers, product_id):
    """Return current stock for a product via admin endpoint."""
    resp = api_session.get(f"{BASE_URL}/admin/products", headers=admin_headers)
    prods = resp.json()
    if isinstance(prods, dict):
        prods = prods.get("products", prods.get("data", []))
    p = next((x for x in prods if (x.get("product_id") or x.get("id")) == product_id), None)
    return p.get("stock_quantity", p.get("stock", p.get("quantity", 0))) if p else 0


# ── GET /orders ──────────────────────────────────────────────────────────────

class TestOrderList:

    def test_get_orders_returns_list(self, api_session, valid_headers):
        """GET /orders must return a list of orders."""
        resp = api_session.get(f"{BASE_URL}/orders", headers=valid_headers)
        assert resp.status_code == 200
        body = resp.json()
        data = body if isinstance(body, list) else body.get("orders", body.get("data", []))
        assert isinstance(data, list)


# ── GET /orders/{id} ─────────────────────────────────────────────────────────

class TestOrderDetail:

    def test_get_order_detail(self, api_session, valid_headers, first_product):
        """GET /orders/{id} for an existing order must return details."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp, body = _place_order(api_session, valid_headers, pid)
        if resp.status_code != 200:
            pytest.skip("Could not place order")
        oid = body.get("order_id") or body.get("id")

        detail_resp = _get_order(api_session, valid_headers, oid)
        assert detail_resp.status_code == 200

    def test_get_nonexistent_order_returns_404(self, api_session, valid_headers):
        """GET /orders/{nonexistent} must return 404."""
        resp = _get_order(api_session, valid_headers, 999999)
        assert resp.status_code == 404


# ── cancel ───────────────────────────────────────────────────────────────────

class TestOrderCancel:

    def test_cancel_pending_order_succeeds(self, api_session, valid_headers,
                                            first_product):
        """Cancelling a PENDING/PLACED order must succeed."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp, body = _place_order(api_session, valid_headers, pid, method="COD")
        if resp.status_code != 200:
            pytest.skip("Could not place COD order")
        oid = body.get("order_id") or body.get("id")

        cancel_resp = api_session.post(
            f"{BASE_URL}/orders/{oid}/cancel", headers=valid_headers
        )
        assert cancel_resp.status_code == 200

    def test_cancel_delivered_order_rejected(self, api_session, valid_headers):
        """Cancelling a DELIVERED order must return 400."""
        resp = api_session.get(f"{BASE_URL}/orders", headers=valid_headers)
        orders = resp.json()
        if isinstance(orders, dict):
            orders = orders.get("orders", orders.get("data", []))
        delivered = [o for o in orders
                     if (o.get("order_status") or o.get("status", "")).upper() == "DELIVERED"]
        if not delivered:
            pytest.skip("No DELIVERED order to test cancellation on")
        oid = delivered[0].get("order_id") or delivered[0].get("id")

        cancel_resp = api_session.post(
            f"{BASE_URL}/orders/{oid}/cancel", headers=valid_headers
        )
        assert cancel_resp.status_code == 400

    def test_cancel_nonexistent_order_returns_404(self, api_session, valid_headers):
        """Cancelling a non-existent order must return 404."""
        resp = api_session.post(
            f"{BASE_URL}/orders/999999/cancel", headers=valid_headers
        )
        assert resp.status_code == 404


# ── stock restoration after cancel ───────────────────────────────────────────

class TestOrderCancelStockRestore:

    def test_cancel_restores_stock(self, api_session, valid_headers,
                                    first_product, admin_headers):
        """After cancellation, product stock must be restored for each item."""
        pid = first_product.get("product_id") or first_product.get("id")
        qty = 2
        stock_before = _get_stock(api_session, admin_headers, pid)

        resp, body = _place_order(api_session, valid_headers, pid, qty=qty, method="COD")
        if resp.status_code != 200:
            pytest.skip("Could not place order")
        oid = body.get("order_id") or body.get("id")

        stock_after_order = _get_stock(api_session, admin_headers, pid)

        # cancel
        cancel_resp = api_session.post(
            f"{BASE_URL}/orders/{oid}/cancel", headers=valid_headers
        )
        assert cancel_resp.status_code == 200

        stock_after_cancel = _get_stock(api_session, admin_headers, pid)
        assert stock_after_cancel == stock_after_order + qty, (
            f"Stock not restored: before_cancel={stock_after_order}, "
            f"after_cancel={stock_after_cancel}, expected +{qty}"
        )


# ── invoice ──────────────────────────────────────────────────────────────────

class TestOrderInvoice:

    def test_invoice_math(self, api_session, valid_headers, first_product):
        """
        Invoice subtotal, gst_amount, and total_amount must satisfy:
          gst_amount = subtotal × 0.05
          total_amount = subtotal + gst_amount
        """
        pid = first_product.get("product_id") or first_product.get("id")
        resp, body = _place_order(api_session, valid_headers, pid, qty=2)
        if resp.status_code != 200:
            pytest.skip("Could not place order")
        oid = body.get("order_id") or body.get("id")

        inv_resp = api_session.get(
            f"{BASE_URL}/orders/{oid}/invoice", headers=valid_headers
        )
        assert inv_resp.status_code == 200
        inv = inv_resp.json()
        inv = inv.get("invoice", inv)

        subtotal = inv.get("subtotal", 0)
        gst = inv.get("gst_amount", inv.get("gst", 0))
        total = inv.get("total_amount", inv.get("total", 0))

        expected_gst = subtotal * 0.05
        expected_total = subtotal + expected_gst

        assert abs(gst - expected_gst) < 0.5, (
            f"GST mismatch: expected {expected_gst}, got {gst}"
        )
        assert abs(total - expected_total) < 0.5, (
            f"Total mismatch: expected {expected_total}, got {total}"
        )
