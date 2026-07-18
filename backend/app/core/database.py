"""
Database connection and utilities.
Uses the Supabase client exclusively. A prior direct-PostgreSQL (asyncpg)
path existed here but was unused by every endpoint and unreachable from
this environment (DATABASE_URL's host does not resolve) - removed to
avoid the two-pattern confusion that was causing 500s (endpoints called
Supabase-style `.table()` methods on a raw asyncpg dependency).
"""

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from app.core.config import settings
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get or create Supabase client."""
    global _supabase_client

    if _supabase_client is None and settings.supabase_available:
        try:
            logger.info(f"Creating Supabase client for: {settings.SUPABASE_URL}")
            # Use SERVICE_KEY for backend operations to bypass RLS
            key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
            # Default postgrest_client_timeout is 5s, too tight for a fresh
            # TLS handshake on a reconnect (idle connections get dropped) -
            # this caused sporadic "An error occurred" on otherwise-working
            # requests like creating a teacher/parent.
            _supabase_client = create_client(
                settings.SUPABASE_URL, key,
                options=ClientOptions(postgrest_client_timeout=20)
            )
            logger.info("Supabase client created successfully")
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            _supabase_client = None

    return _supabase_client


def test_supabase_connection() -> bool:
    """Test Supabase connection."""
    try:
        client = get_supabase()
        if not client:
            return False

        client.table("users").select("count", count="exact").limit(1).execute()
        return True
    except Exception as e:
        logger.error("Supabase connection test failed: %s", e)
        return False


def initialize_database():
    """Initialize database connections (Supabase only)."""
    logger.info("Initializing database connections...")

    if settings.supabase_available:
        if test_supabase_connection():
            logger.info("✅ Supabase connection established")
        else:
            logger.warning("⚠️  Supabase connection test failed")
    else:
        logger.error("❌ Supabase not configured (SUPABASE_URL/SUPABASE_SERVICE_KEY missing)")


def cleanup_database() -> None:
    """Clean up database connections. No-op for the Supabase REST client."""
    logger.info("Database cleanup complete")


def check_database_health() -> Dict[str, Any]:
    """Check database health status."""
    health = {
        "supabase": {
            "available": False,
            "error": None
        },
        "overall": False
    }

    try:
        client = get_supabase()
        if client and test_supabase_connection():
            health["supabase"]["available"] = True
        else:
            health["supabase"]["error"] = "Connection failed or not configured"
    except Exception as e:
        health["supabase"]["error"] = str(e)

    health["overall"] = health["supabase"]["available"]

    return health
