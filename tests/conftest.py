"""Shared fixtures for the Date Drop test suite."""

import os
from unittest.mock import MagicMock

import pytest

# Set test environment variables before importing the app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-that-is-long-enough")
os.environ.setdefault("ADMIN_SECRET", "test-admin-secret")
os.environ.setdefault("RESEND_API_KEY", "re_test_key")
os.environ.setdefault("APP_URL", "http://localhost:8765")


@pytest.fixture()
def mock_supabase():
    """Mock the Supabase client by setting the module-level _client global.

    Route modules import get_supabase via `from app.supabase_client import get_supabase`,
    so they hold a reference to the original function. Setting _client directly ensures
    the original function returns our mock without trying to create a real client.
    """
    import app.supabase_client as sc

    mock_client = MagicMock()
    mock_client.table.return_value = MagicMock()

    original_client = sc._client
    sc._client = mock_client
    yield mock_client
    sc._client = original_client


@pytest.fixture()
def app(mock_supabase):
    """Create the Flask app in test mode."""
    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def auth_headers():
    """Generate a valid JWT token for authenticated requests."""
    import jwt
    from app.config import Config

    token = jwt.encode(
        {"sub": "test-user-id", "email": "test@stu.pku.edu.cn", "aud": "authenticated"},
        Config.SUPABASE_JWT_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers():
    """Headers for admin API requests."""
    return {"X-Admin-Key": "test-admin-secret"}
