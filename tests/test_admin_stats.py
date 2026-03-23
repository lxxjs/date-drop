"""Tests for the admin stats endpoint."""

from unittest.mock import MagicMock


class TestAdminStats:
    """GET /api/admin/stats"""

    def test_stats_success(self, client, admin_headers, mock_supabase):
        table = mock_supabase.table.return_value

        # Mock all the count queries
        profiles_count = MagicMock()
        profiles_count.count = 42

        invites_total = MagicMock()
        invites_total.count = 20

        invites_used = MagicMock()
        invites_used.count = 8

        matches_total = MagicMock()
        matches_total.count = 15

        matches_accepted = MagicMock()
        matches_accepted.count = 10

        messages_result = MagicMock()
        messages_result.data = [
            {"match_id": "m1"},
            {"match_id": "m1"},
            {"match_id": "m2"},
        ]

        quick_match_count = MagicMock()
        quick_match_count.count = 5

        # Set up the chain — multiple select().execute() calls
        table.select.return_value.execute.side_effect = [
            profiles_count,
            invites_total,
            invites_used,
            matches_total,
            matches_accepted,
            messages_result,
            quick_match_count,
        ]
        table.select.return_value.not_.is_.return_value.execute.return_value = invites_used
        table.select.return_value.eq.return_value.execute.side_effect = [
            matches_accepted,
            quick_match_count,
        ]

        resp = client.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "stats" in data
        assert "signup_count" in data["stats"]
        assert "invite_conversion_pct" in data["stats"]

    def test_stats_unauthorized(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 403

    def test_stats_wrong_key(self, client):
        resp = client.get("/api/admin/stats", headers={"X-Admin-Key": "wrong"})
        assert resp.status_code == 403
