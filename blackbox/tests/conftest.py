"""
Shared fixtures for QuickCart black-box test suite.

Provides:
  - BASE_URL, ROLL_NUMBER constants
  - valid_headers / admin_headers fixtures
  - setup_user (session-scoped) — discovers first user via admin endpoint
  - clean_cart — empties the cart before tests that need it
  - funded_wallet — ensures ≥ 10 000 in wallet for checkout tests

NOTE: The QuickCart server is an ARM64 image running under QEMU on AMD64,
      so it is fragile. We add automatic retry with backoff and small delays
      between tests to keep it alive.
"""

import time
import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── constants ────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8080/api/v1"
ROLL_NUMBER = "2024113015"

# ── rate-limiting hook ───────────────────────────────────────────────────────
def pytest_runtest_teardown(item, nextitem):
    """Add a small delay between tests to avoid overwhelming the server."""
    time.sleep(0.15)


# ── reusable session with retry ──────────────────────────────────────────────
@pytest.fixture(scope="session")
def api_session():
    """A requests.Session with automatic retry on connection failures."""
    s = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    yield s
    s.close()


# ── header fixtures ──────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def admin_headers():
    """Headers for admin-only endpoints (no X-User-ID)."""
    return {
        "X-Roll-Number": ROLL_NUMBER,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def setup_user(api_session, admin_headers):
    """
    Session-scoped fixture that:
      1. Calls GET /admin/users to discover the first available user.
      2. Builds per-user headers containing both X-Roll-Number and X-User-ID.
      3. Returns {"user_id": <id>, "headers": {…}}.
    """
    resp = api_session.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    assert resp.status_code == 200, f"Failed to fetch admin users: {resp.text}"
    users = resp.json()
    # Handle both list and dict-wrapped responses
    if isinstance(users, dict):
        users = users.get("users", users.get("data", []))
    assert len(users) > 0, "No users found via /admin/users"

    first_user = users[0]
    user_id = str(first_user.get("user_id") or first_user.get("id"))

    headers = {
        "X-Roll-Number": ROLL_NUMBER,
        "X-User-ID": user_id,
        "Content-Type": "application/json",
    }
    return {"user_id": user_id, "headers": headers}


@pytest.fixture
def valid_headers(setup_user):
    """Convenience alias — returns the per-user headers dict."""
    return setup_user["headers"].copy()


# ── cart helpers ─────────────────────────────────────────────────────────────
@pytest.fixture
def clean_cart(api_session, valid_headers):
    """Clears the cart before the test runs."""
    api_session.delete(f"{BASE_URL}/cart/clear", headers=valid_headers)
    yield
    # also clean up after
    api_session.delete(f"{BASE_URL}/cart/clear", headers=valid_headers)


# ── wallet helpers ───────────────────────────────────────────────────────────
@pytest.fixture
def funded_wallet(api_session, valid_headers):
    """
    Ensures the wallet has at least 10 000 before the test.
    Adds 10 000 unconditionally (the tests that use this need a funded wallet).
    """
    api_session.post(
        f"{BASE_URL}/wallet/add",
        headers=valid_headers,
        json={"amount": 10000},
    )
    yield


# ── product helpers ──────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def first_product(api_session, setup_user):
    """Returns the first active product dict (cached for the session)."""
    resp = api_session.get(
        f"{BASE_URL}/products", headers=setup_user["headers"]
    )
    assert resp.status_code == 200
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", products.get("data", []))
    assert len(products) > 0, "No active products found"
    return products[0]


@pytest.fixture(scope="session")
def all_products(api_session, setup_user):
    """Returns the full list of active products (cached for the session)."""
    resp = api_session.get(
        f"{BASE_URL}/products", headers=setup_user["headers"]
    )
    assert resp.status_code == 200
    products = resp.json()
    if isinstance(products, dict):
        products = products.get("products", products.get("data", []))
    return products
