from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        from app.config import Config

        if not Config.SUPABASE_URL or not Config.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "Create a Supabase project and add the keys to your .env file."
            )
        _client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
    return _client


class _EmptyResult:
    """Stand-in when maybe_single() returns None (no matching row)."""
    data = None


def exec_single(query):
    """Run query.maybe_single().execute() safely.

    Returns a result whose .data is either a dict (row found) or None.
    """
    result = query.maybe_single().execute()
    return result if result is not None else _EmptyResult()
