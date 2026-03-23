"""
Tests for the Support Ticket endpoints:
  POST /support/ticket, GET /support/tickets,
  PUT /support/tickets/{id}

Covers subject/message validation, initial status,
message fidelity, and status-transition rules.
"""

import pytest
from .conftest import BASE_URL


# ── helpers ──────────────────────────────────────────────────────────────────

def _create_ticket(api_session, headers, subject="Test Issue Title", message="Please help me."):
    return api_session.post(
        f"{BASE_URL}/support/ticket",
        headers=headers,
        json={"subject": subject, "message": message},
    )


def _update_ticket_status(api_session, headers, ticket_id, status):
    return api_session.put(
        f"{BASE_URL}/support/tickets/{ticket_id}",
        headers=headers,
        json={"status": status},
    )


def _get_ticket_id(body):
    """Extract ticket_id from creation response."""
    t = body.get("ticket", body)
    return t.get("ticket_id") or t.get("id")


# ── creation validation ─────────────────────────────────────────────────────

class TestTicketCreation:

    def test_valid_ticket_created(self, api_session, valid_headers):
        """POST with valid subject (5–100) and message (1–500) must succeed."""
        resp = _create_ticket(api_session, valid_headers)
        assert resp.status_code in (200, 201)

    @pytest.mark.parametrize("short_subj", ["abcd", "abc", "ab", "a", ""])
    def test_subject_too_short_rejected(self, api_session, valid_headers, short_subj):
        """Subject < 5 characters must be rejected."""
        resp = _create_ticket(api_session, valid_headers, subject=short_subj)
        assert resp.status_code == 400

    def test_subject_too_long_rejected(self, api_session, valid_headers):
        """Subject > 100 characters must be rejected."""
        resp = _create_ticket(api_session, valid_headers, subject="X" * 101)
        assert resp.status_code == 400

    def test_subject_exactly_5_chars_succeeds(self, api_session, valid_headers):
        """Subject length == 5 must succeed."""
        resp = _create_ticket(api_session, valid_headers, subject="12345")
        assert resp.status_code == 200

    def test_subject_exactly_100_chars_succeeds(self, api_session, valid_headers):
        """Subject length == 100 must succeed."""
        long_subject = "A" * 100
        resp = _create_ticket(api_session, valid_headers, subject=long_subject)
        assert resp.status_code == 200


    def test_message_empty_rejected(self, api_session, valid_headers):
        """Empty message must be rejected."""
        resp = _create_ticket(api_session, valid_headers, subject="12345", message="")
        assert resp.status_code == 400

    def ___dummy(self, api_session, valid_headers):
        """Message < 1 character must be rejected."""
        resp = _create_ticket(api_session, valid_headers, message="")
        assert resp.status_code == 400

    def test_message_too_long_rejected(self, api_session, valid_headers):
        """Message > 500 characters must be rejected."""
        resp = _create_ticket(api_session, valid_headers, message="M" * 501)
        assert resp.status_code == 400


class TestTicketInitialStatus:

    def test_new_ticket_status_open(self, api_session, valid_headers):
        """A newly created ticket must have status OPEN."""
        resp = _create_ticket(api_session, valid_headers,
                               subject="Status Check Test")
        assert resp.status_code in (200, 201)
        body = resp.json()
        ticket = body.get("ticket", body)
        assert ticket.get("status", "").upper() == "OPEN"


class TestTicketMessageFidelity:

    def test_message_saved_exactly(self, api_session, valid_headers):
        """The full message must be saved exactly as submitted (no truncation).
        BUG: Server truncates messages."""
        msg = "This is a detailed message for the support team."
        resp = _create_ticket(api_session, valid_headers,
                               subject="Fidelity Test Subj",
                               message=msg)
        assert resp.status_code in (200, 201)
        body = resp.json()
        ticket = body.get("ticket", body)
        saved = ticket.get("message", ticket.get("description", ""))
        assert saved == msg, (
            f"BUG: Message was truncated or altered. "
            f"Sent {len(msg)} chars, got back: '{saved}'"
        )


# ── status transitions ──────────────────────────────────────────────────────

class TestTicketStatusTransitions:

    def _fresh_ticket(self, api_session, headers):
        """Create a new OPEN ticket and return its id."""
        resp = _create_ticket(api_session, headers, subject="Transition Test Ticket")
        assert resp.status_code in (200, 201)
        return _get_ticket_id(resp.json())

    def test_open_to_in_progress(self, api_session, valid_headers):
        """OPEN → IN_PROGRESS must succeed."""
        tid = self._fresh_ticket(api_session, valid_headers)
        resp = _update_ticket_status(api_session, valid_headers, tid, "IN_PROGRESS")
        assert resp.status_code == 200

    def test_in_progress_to_closed(self, api_session, valid_headers):
        """IN_PROGRESS → CLOSED must succeed."""
        tid = self._fresh_ticket(api_session, valid_headers)
        _update_ticket_status(api_session, valid_headers, tid, "IN_PROGRESS")
        resp = _update_ticket_status(api_session, valid_headers, tid, "CLOSED")
        assert resp.status_code == 200

    def test_open_to_closed_rejected(self, api_session, valid_headers):
        """OPEN → CLOSED (skipping IN_PROGRESS) must fail."""
        tid = self._fresh_ticket(api_session, valid_headers)
        resp = _update_ticket_status(api_session, valid_headers, tid, "CLOSED")
        assert resp.status_code >= 400

    def test_closed_to_in_progress_rejected(self, api_session, valid_headers):
        """CLOSED → IN_PROGRESS must fail (cannot reopen)."""
        tid = self._fresh_ticket(api_session, valid_headers)
        _update_ticket_status(api_session, valid_headers, tid, "IN_PROGRESS")
        _update_ticket_status(api_session, valid_headers, tid, "CLOSED")
        resp = _update_ticket_status(api_session, valid_headers, tid, "IN_PROGRESS")
        assert resp.status_code >= 400

    def test_closed_to_open_rejected(self, api_session, valid_headers):
        """CLOSED → OPEN must fail."""
        tid = self._fresh_ticket(api_session, valid_headers)
        _update_ticket_status(api_session, valid_headers, tid, "IN_PROGRESS")
        _update_ticket_status(api_session, valid_headers, tid, "CLOSED")
        resp = _update_ticket_status(api_session, valid_headers, tid, "OPEN")
        assert resp.status_code >= 400
