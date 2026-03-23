"""
Tests for the Reviews endpoints:
  GET  /products/{id}/reviews
  POST /products/{id}/reviews

Covers rating boundaries (1–5), comment length boundaries (1–200),
average-rating decimal calculation, and zero-reviews edge case.
"""

import pytest
from .conftest import BASE_URL


def _post_review(api_session, headers, product_id, rating, comment="Good product"):
    return api_session.post(
        f"{BASE_URL}/products/{product_id}/reviews",
        headers=headers,
        json={"rating": rating, "comment": comment},
    )


def _get_reviews(api_session, headers, product_id):
    resp = api_session.get(
        f"{BASE_URL}/products/{product_id}/reviews", headers=headers
    )
    return resp


# ── rating boundaries ────────────────────────────────────────────────────────

class TestReviewRating:

    @pytest.mark.parametrize("rating", [1, 5])
    def test_valid_boundary_ratings_accepted(self, api_session, valid_headers,
                                              first_product, rating):
        """Ratings 1 (min) and 5 (max) must be accepted."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, rating,
                            comment=f"Rating {rating} test")
        assert resp.status_code in (200, 201), (
            f"Rating {rating} rejected: {resp.status_code}"
        )

    @pytest.mark.parametrize("rating", [0, -1, 6, 100])
    def test_invalid_ratings_rejected(self, api_session, valid_headers,
                                       first_product, rating):
        """Ratings outside 1–5 must be rejected with 400."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, rating)
        assert resp.status_code == 400


# ── comment length boundaries ────────────────────────────────────────────────

class TestReviewComment:

    def test_comment_length_1_accepted(self, api_session, valid_headers, first_product):
        """Boundary: 1-char comment must succeed."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, 3, comment="A")
        assert resp.status_code in (200, 201)

    def test_comment_length_200_accepted(self, api_session, valid_headers, first_product):
        """Boundary: 200-char comment must succeed."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, 3, comment="A" * 200)
        assert resp.status_code in (200, 201)

    def test_comment_length_0_rejected(self, api_session, valid_headers, first_product):
        """Empty comment (len=0) must be rejected with 400."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, 3, comment="")
        assert resp.status_code == 400

    def test_comment_length_201_rejected(self, api_session, valid_headers, first_product):
        """Comment exceeding 200 chars must be rejected with 400."""
        pid = first_product.get("product_id") or first_product.get("id")
        resp = _post_review(api_session, valid_headers, pid, 3, comment="B" * 201)
        assert resp.status_code == 400


# ── average rating ───────────────────────────────────────────────────────────

class TestReviewAverage:

    def test_no_reviews_average_is_zero(self, api_session, valid_headers, all_products):
        """If a product has no reviews, average_rating must be 0 (not null)."""
        # Attempt to find a product with no reviews
        for p in all_products:
            pid = p.get("product_id") or p.get("id")
            resp = _get_reviews(api_session, valid_headers, pid)
            if resp.status_code != 200:
                continue
            body = resp.json()
            reviews = body.get("reviews", body.get("data", body))
            if isinstance(reviews, list) and len(reviews) == 0:
                avg = body.get("average_rating", body.get("avg_rating"))
                assert avg is not None, "average_rating is missing (should be 0)"
                assert float(avg) == 0, f"Expected 0, got {avg}"
                return
        pytest.skip("All products already have reviews")

    def test_average_rating_is_decimal(self, api_session, valid_headers, first_product):
        """Average rating must be a proper decimal = sum(ratings)/count."""
        pid = first_product.get("product_id") or first_product.get("id")
        # post two reviews with distinct ratings to get a non-integer avg
        _post_review(api_session, valid_headers, pid, 2, comment="Review calcA")
        _post_review(api_session, valid_headers, pid, 5, comment="Review calcB")

        resp = _get_reviews(api_session, valid_headers, pid)
        assert resp.status_code == 200
        body = resp.json()
        reviews = body.get("reviews", body.get("data", body))
        if isinstance(reviews, list) and len(reviews) > 0:
            ratings = [r.get("rating") for r in reviews if r.get("rating") is not None]
            expected_avg = sum(ratings) / len(ratings)
            actual_avg = body.get("average_rating", body.get("avg_rating", 0))
            assert abs(float(actual_avg) - expected_avg) < 0.01, (
                f"Avg mismatch: expected {expected_avg}, got {actual_avg}"
            )
