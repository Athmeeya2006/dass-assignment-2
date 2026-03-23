"""
Tests for the Products endpoints:
  GET /products, GET /products/{product_id}

Covers active-only listing, single lookup, filtering, sorting,
and price accuracy.
"""

import pytest
from .conftest import BASE_URL


def _get_products(api_session, headers, **params):
    """GET /products with optional query params; returns the list."""
    resp = api_session.get(f"{BASE_URL}/products", headers=headers, params=params)
    assert resp.status_code == 200
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("products", body.get("data", []))


class TestProductListing:

    def test_returns_only_active_products(self, api_session, valid_headers, admin_headers):
        """The public list must contain only active products."""
        public = _get_products(api_session, valid_headers)
        # check via admin that no inactive product appears
        admin_resp = api_session.get(f"{BASE_URL}/admin/products", headers=admin_headers)
        all_prods = admin_resp.json()
        if isinstance(all_prods, dict):
            all_prods = all_prods.get("products", all_prods.get("data", []))
        inactive_ids = {
            (p.get("product_id") or p.get("id"))
            for p in all_prods
            if not p.get("is_active", True) and p.get("active", True) is False
               or p.get("is_active") is False
        }
        public_ids = {(p.get("product_id") or p.get("id")) for p in public}
        overlap = public_ids & inactive_ids
        assert not overlap, f"Inactive products in public list: {overlap}"

    def test_single_product_valid_id(self, api_session, valid_headers, first_product):
        """GET /products/{id} for a valid product returns its data with price."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = api_session.get(f"{BASE_URL}/products/{pid}", headers=valid_headers)
        assert resp.status_code == 200
        body = resp.json()
        data = body.get("product", body) if isinstance(body, dict) else body
        assert "price" in data, "Product response missing 'price' field"

    def test_single_product_nonexistent_returns_404(self, api_session, valid_headers):
        """GET /products/{id} for a non-existent id must return 404."""
        resp = api_session.get(f"{BASE_URL}/products/999999", headers=valid_headers)
        assert resp.status_code == 404


class TestProductFiltering:

    def test_filter_by_category(self, api_session, valid_headers, all_products):
        """GET /products?category=X should return only products of that category."""
        if not all_products:
            pytest.skip("No products available")
        cat = all_products[0].get("category")
        if not cat:
            pytest.skip("Product has no category field")
        filtered = _get_products(api_session, valid_headers, category=cat)
        for p in filtered:
            assert p.get("category") == cat, f"Expected category={cat}, got {p.get('category')}"

    def test_search_by_name(self, api_session, valid_headers, first_product):
        """GET /products?search=<name> should return matching products."""
        name = first_product.get("name", "")
        if not name:
            pytest.skip("Product has no name field")
        keyword = name.split()[0] if " " in name else name[:4]
        results = _get_products(api_session, valid_headers, search=keyword)
        assert len(results) >= 1, f"Search for '{keyword}' returned no results"

    def test_sort_price_ascending(self, api_session, valid_headers):
        """sort=price_asc must return prices in ascending order."""
        products = _get_products(api_session, valid_headers, sort="price_asc")
        prices = [p["price"] for p in products if "price" in p]
        assert prices == sorted(prices), "Prices not in ascending order"

    def test_sort_price_descending(self, api_session, valid_headers):
        """sort=price_desc must return prices in descending order."""
        products = _get_products(api_session, valid_headers, sort="price_desc")
        prices = [p["price"] for p in products if "price" in p]
        assert prices == sorted(prices, reverse=True), "Prices not in descending order"


class TestProductPriceAccuracy:

    def test_price_matches_admin(self, api_session, valid_headers, admin_headers, first_product):
        """Price from public endpoint must match admin endpoint exactly."""
        pid = first_product.get("product_id") or first_product.get("id")
        public_resp = api_session.get(f"{BASE_URL}/products/{pid}", headers=valid_headers)
        public_data = public_resp.json()
        public_data = public_data.get("product", public_data) if isinstance(public_data, dict) else public_data

        admin_resp = api_session.get(f"{BASE_URL}/admin/products", headers=admin_headers)
        admin_all = admin_resp.json()
        if isinstance(admin_all, dict):
            admin_all = admin_all.get("products", admin_all.get("data", []))
        admin_prod = next(
            (p for p in admin_all if (p.get("product_id") or p.get("id")) == pid),
            None,
        )
        assert admin_prod is not None, "Product not found in admin list"
        assert float(public_data["price"]) == float(admin_prod["price"]), (
            f"Price mismatch: public={public_data['price']}, admin={admin_prod['price']}"
        )
