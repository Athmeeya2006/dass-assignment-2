"""
Tests for the Admin endpoints:
  GET /admin/users, GET /admin/users/{id}, GET /admin/carts,
  GET /admin/orders, GET /admin/products, GET /admin/coupons,
  GET /admin/tickets, GET /admin/addresses

Verifies data presence, admin-vs-public product count,
and X-Roll-Number requirement.
"""

import pytest
from .conftest import BASE_URL, ROLL_NUMBER


class TestAdminUsers:

    def test_admin_users_returns_list_with_balance_and_points(
        self, api_session, admin_headers
    ):
        """GET /admin/users must return users with wallet_balance and loyalty_points."""
        resp = api_session.get(f"{BASE_URL}/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        users = body if isinstance(body, list) else body.get("users", body.get("data", []))
        assert len(users) > 0, "No users returned"
        u = users[0]
        assert (
            "wallet_balance" in u or "balance" in u
        ), "User missing wallet balance"
        assert (
            "loyalty_points" in u or "points" in u
        ), "User missing loyalty points"

    def test_admin_single_user(self, api_session, admin_headers, setup_user):
        """GET /admin/users/{id} must return a single user."""
        uid = setup_user["user_id"]
        resp = api_session.get(
            f"{BASE_URL}/admin/users/{uid}", headers=admin_headers
        )
        assert resp.status_code == 200


class TestAdminCarts:

    def test_admin_carts_returns_data(self, api_session, admin_headers):
        """GET /admin/carts must return a list of carts."""
        resp = api_session.get(f"{BASE_URL}/admin/carts", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminOrders:

    def test_admin_orders_returns_data(self, api_session, admin_headers):
        """GET /admin/orders must return a list of orders."""
        resp = api_session.get(f"{BASE_URL}/admin/orders", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminProducts:

    def test_admin_products_includes_inactive(self, api_session, admin_headers,
                                               valid_headers):
        """
        Admin product count must be ≥ public product count,
        because admin includes inactive products too.
        """
        admin_resp = api_session.get(
            f"{BASE_URL}/admin/products", headers=admin_headers
        )
        public_resp = api_session.get(
            f"{BASE_URL}/products", headers=valid_headers
        )
        assert admin_resp.status_code == 200
        assert public_resp.status_code == 200

        admin_prods = admin_resp.json()
        if isinstance(admin_prods, dict):
            admin_prods = admin_prods.get("products", admin_prods.get("data", []))
        public_prods = public_resp.json()
        if isinstance(public_prods, dict):
            public_prods = public_prods.get("products", public_prods.get("data", []))

        assert len(admin_prods) >= len(public_prods), (
            f"Admin products ({len(admin_prods)}) < public ({len(public_prods)})"
        )


class TestAdminCoupons:

    def test_admin_coupons_returns_data(self, api_session, admin_headers):
        """GET /admin/coupons returns all coupons including expired."""
        resp = api_session.get(f"{BASE_URL}/admin/coupons", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminTickets:

    def test_admin_tickets_returns_data(self, api_session, admin_headers):
        """GET /admin/tickets returns all support tickets."""
        resp = api_session.get(f"{BASE_URL}/admin/tickets", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminAddresses:

    def test_admin_addresses_returns_data(self, api_session, admin_headers):
        """GET /admin/addresses returns all addresses."""
        resp = api_session.get(f"{BASE_URL}/admin/addresses", headers=admin_headers)
        assert resp.status_code == 200


class TestAdminAuthRequired:

    def test_admin_endpoint_requires_roll_number(self, api_session):
        """All admin endpoints require X-Roll-Number; missing ⇒ 401."""
        resp = api_session.get(
            f"{BASE_URL}/admin/users",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401
