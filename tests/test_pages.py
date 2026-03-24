"""Tests for page routes including invite landing page."""


class TestInviteLandingPage:
    """GET /invite/<code>"""

    def test_invite_page_renders(self, client, mock_supabase):
        resp = client.get("/invite/abc12345")
        assert resp.status_code == 200
        assert b"date drop" in resp.data.lower()
        assert b"abc12345" in resp.data

    def test_invite_page_injects_code(self, client, mock_supabase):
        resp = client.get("/invite/xyz99999")
        assert resp.status_code == 200
        assert b"xyz99999" in resp.data


class TestExistingPages:
    """Smoke tests for existing pages."""

    def test_index(self, client, mock_supabase):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home(self, client, mock_supabase):
        resp = client.get("/home")
        assert resp.status_code == 200

    def test_questions(self, client, mock_supabase):
        resp = client.get("/questions")
        assert resp.status_code == 200
        # Quick match toggle should be present
        assert b"matchMode" in resp.data

    def test_cupid(self, client, mock_supabase):
        resp = client.get("/cupid")
        assert resp.status_code == 200
