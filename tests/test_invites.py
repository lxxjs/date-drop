"""Tests for the invite link system."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


def _mock_execute_sequence(mock_supabase, results):
    """Set up a sequence of .execute() return values across all chains.

    Since all table() calls share the same mock, we use side_effect on the
    terminal .execute() to return results in order.
    """
    # Collect all possible execute endpoints and set side_effect
    table = mock_supabase.table.return_value
    chain = table.select.return_value
    # All possible chain endings go through .execute()
    execute_mock = MagicMock(side_effect=results)

    # Wire up every chain path to the same execute mock
    chain.eq.return_value.maybe_single.return_value.execute = execute_mock
    chain.eq.return_value.execute = execute_mock
    chain.eq.return_value.order.return_value.execute = execute_mock
    chain.execute = execute_mock
    chain.not_.is_.return_value.execute = execute_mock
    table.insert.return_value.execute = execute_mock
    table.update.return_value.eq.return_value.execute = execute_mock

    return execute_mock


def _make_result(data=None, count=None):
    r = MagicMock()
    r.data = data
    r.count = count
    return r


class TestCreateInvite:
    """POST /api/invite/create"""

    def test_create_invite_success(self, client, auth_headers, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            # 1. Profile lookup
            _make_result(data={"id": "profile-123", "school_id": "school-1"}),
            # 2. Quota check
            _make_result(count=0),
            # 3. Insert
            _make_result(data={"id": "inv-1"}),
        ])

        resp = client.post("/api/invite/create", headers=auth_headers)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["ok"] is True
        assert "invite_code" in data
        assert "expires_at" in data

    def test_create_invite_no_profile(self, client, auth_headers, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            _make_result(data=None),  # No profile
        ])

        resp = client.post("/api/invite/create", headers=auth_headers)
        assert resp.status_code == 400
        assert "profile" in resp.get_json()["message"].lower()

    def test_create_invite_quota_exceeded(self, client, auth_headers, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            _make_result(data={"id": "profile-123", "school_id": "school-1"}),
            _make_result(count=5),  # At the limit
        ])

        resp = client.post("/api/invite/create", headers=auth_headers)
        assert resp.status_code == 400
        assert "maximum" in resp.get_json()["message"].lower()

    def test_create_invite_unauthenticated(self, client):
        resp = client.post("/api/invite/create")
        assert resp.status_code == 401


class TestGetInvite:
    """GET /api/invite/<code>"""

    def test_get_valid_invite(self, client, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            # 1. Invite lookup
            _make_result(data={
                "id": "inv-1", "invite_code": "abc12345",
                "used_by": None, "expires_at": future, "inviter_id": "profile-123",
            }),
            # 2. Inviter profile (school_id)
            _make_result(data={"school_id": "school-1"}),
            # 3. School name
            _make_result(data={"name": "Peking University"}),
            # 4. Profile count for social proof
            _make_result(count=25),
        ])

        resp = client.get("/api/invite/abc12345")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["school_name"] == "Peking University"
        assert "social_proof" in data

    def test_get_invalid_invite(self, client, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            _make_result(data=None),
        ])

        resp = client.get("/api/invite/nonexistent")
        assert resp.status_code == 404

    def test_get_expired_invite(self, client, mock_supabase):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={
                "id": "inv-1", "invite_code": "expired1",
                "used_by": None, "expires_at": past, "inviter_id": "profile-123",
            }),
        ])

        resp = client.get("/api/invite/expired1")
        assert resp.status_code == 410
        assert "expired" in resp.get_json()["message"].lower()

    def test_get_used_invite(self, client, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={
                "id": "inv-1", "invite_code": "used1234",
                "used_by": "profile-456", "expires_at": future,
                "inviter_id": "profile-123",
            }),
        ])

        resp = client.get("/api/invite/used1234")
        assert resp.status_code == 410
        assert "already been used" in resp.get_json()["message"].lower()

    def test_social_proof_below_10(self, client, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={
                "id": "inv-1", "invite_code": "abc12345",
                "used_by": None, "expires_at": future, "inviter_id": "profile-123",
            }),
            _make_result(data={"school_id": "school-1"}),
            _make_result(data={"name": "Tsinghua University"}),
            _make_result(count=5),  # Below threshold
        ])

        resp = client.get("/api/invite/abc12345")
        data = resp.get_json()
        assert "Be one of the first" in data["social_proof"]

    def test_social_proof_above_100(self, client, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={
                "id": "inv-1", "invite_code": "abc12345",
                "used_by": None, "expires_at": future, "inviter_id": "profile-123",
            }),
            _make_result(data={"school_id": "school-1"}),
            _make_result(data={"name": "PKU"}),
            _make_result(count=150),
        ])

        resp = client.get("/api/invite/abc12345")
        data = resp.get_json()
        assert "100+" in data["social_proof"]


class TestRedeemInvite:
    """POST /api/invite/redeem"""

    def test_redeem_success(self, client, auth_headers, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            # 1. Redeemer profile
            _make_result(data={"id": "profile-new"}),
            # 2. Invite lookup
            _make_result(data={
                "id": "inv-1", "inviter_id": "profile-123",
                "used_by": None, "expires_at": future,
            }),
            # 3. Update invite (mark used)
            _make_result(data=None),
            # 4. Inviter name lookup
            _make_result(data={"full_name": "Alice"}),
        ])

        resp = client.post(
            "/api/invite/redeem",
            json={"invite_code": "abc12345"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["inviter_name"] == "Alice"

    def test_redeem_self_invite(self, client, auth_headers, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={"id": "profile-123"}),
            _make_result(data={
                "id": "inv-1", "inviter_id": "profile-123",
                "used_by": None, "expires_at": future,
            }),
        ])

        resp = client.post(
            "/api/invite/redeem",
            json={"invite_code": "myown123"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "own invite" in resp.get_json()["message"].lower()

    def test_redeem_missing_code(self, client, auth_headers):
        resp = client.post(
            "/api/invite/redeem",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_redeem_no_profile(self, client, auth_headers, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            _make_result(data=None),  # No profile
        ])

        resp = client.post(
            "/api/invite/redeem",
            json={"invite_code": "abc12345"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_redeem_expired_invite(self, client, auth_headers, mock_supabase):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        _mock_execute_sequence(mock_supabase, [
            _make_result(data={"id": "profile-new"}),
            _make_result(data={
                "id": "inv-1", "inviter_id": "profile-123",
                "used_by": None, "expires_at": past,
            }),
        ])

        resp = client.post(
            "/api/invite/redeem",
            json={"invite_code": "expired1"},
            headers=auth_headers,
        )
        assert resp.status_code == 410


class TestMyInvites:
    """GET /api/invite/mine"""

    def test_list_invites(self, client, auth_headers, mock_supabase):
        future = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        now = datetime.now(timezone.utc).isoformat()

        _mock_execute_sequence(mock_supabase, [
            # 1. Profile lookup
            _make_result(data={"id": "profile-123"}),
            # 2. Invites list
            _make_result(data=[
                {"invite_code": "code1111", "used_by": None, "created_at": now, "expires_at": future},
                {"invite_code": "code2222", "used_by": "profile-456", "created_at": now, "expires_at": future},
            ]),
        ])

        resp = client.get("/api/invite/mine", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert len(data["invites"]) == 2
        assert data["remaining"] == 3  # 5 - 2

    def test_list_invites_no_profile(self, client, auth_headers, mock_supabase):
        _mock_execute_sequence(mock_supabase, [
            _make_result(data=None),
        ])

        resp = client.get("/api/invite/mine", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["invites"] == []
