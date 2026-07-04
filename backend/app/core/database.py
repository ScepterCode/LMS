"""
Database connection and utilities.
Supports both direct PostgreSQL connection and Supabase client fallback.
"""

import asyncpg
from supabase import create_client, Client
from app.core.config import settings
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None
_supabase_client: Optional[Client] = None


# ============================================
# POSTGRESQL CONNECTION (Direct)
# ============================================

async def get_db_pool() -> asyncpg.Pool:
    """Get or create PostgreSQL connection pool."""
    global _db_pool
    
    if _db_pool is None and settings.database_available:
        try:
            # Parse connection parameters
            # Note: asyncpg expects connection parameters separately, not a URL
            logger.info("Creating database connection pool...")
            
            # Parse the URL
            if not settings.DATABASE_URL or "YOUR_PASSWORD" in settings.DATABASE_URL or "YOUR_PROJECT" in settings.DATABASE_URL:
                logger.warning("DATABASE_URL not configured - skipping asyncpg pool creation")
                logger.info("Using Supabase client only for database operations")
                return None
            
            result = urlparse(settings.DATABASE_URL)
            
            # Extract connection parameters
            dbname = result.path[1:]  # Remove leading slash
            user = result.username
            password = result.password
            host = result.hostname
            port = result.port or 5432
            
            # Create connection pool
            _db_pool = await asyncpg.create_pool(
                database=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            
            logger.info("Database pool created with %d connections", _db_pool.get_size())
            
        except asyncpg.PostgresError as e:
            logger.error("Failed to create database pool: %s", e)
            logger.warning("Continuing with Supabase client only")
            return None
        except Exception as e:
            logger.error("Unexpected error creating database pool: %s", e)
            logger.warning("Continuing with Supabase client only")
            return None
            _db_pool = None
            raise
    
    return _db_pool


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _db_pool
    
    if _db_pool:
        try:
            await _db_pool.close()
        except (asyncpg.PostgresError, RuntimeError) as e:
            logger.warning("Error closing database pool: %s", e)
        finally:
            _db_pool = None
            logger.info("Database pool closed")


@asynccontextmanager
async def get_db():
    """Context manager for database connections."""
    pool = await get_db_pool()
    if not pool:
        raise ConnectionError("Database pool not available")
    
    async with pool.acquire() as connection:
        try:
            yield connection
        finally:
            await connection.close()


async def test_db_connection() -> bool:
    """Test database connection."""
    try:
        pool = await get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except (asyncpg.PostgresError, ConnectionError) as e:
        logger.error("Database connection test failed: %s", e)
        return False


# ============================================
# SUPABASE CLIENT (Fallback)
# ============================================

def get_supabase() -> Client:
    """Get or create Supabase client."""
    global _supabase_client
    
    if _supabase_client is None and settings.supabase_available:
        try:
            logger.info(f"Creating Supabase client for: {settings.SUPABASE_URL}")
            # Use SERVICE_KEY for backend operations to bypass RLS
            key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
            # Create client with only required parameters (no proxy parameter)
            _supabase_client = create_client(settings.SUPABASE_URL, key)
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
        
        # Try a simple query
        client.table("users").select("count", count="exact").limit(1).execute()
        return True
    except ValueError as e:
        logger.error("Supabase connection test failed: %s", e)
        return False


# ============================================
# UNIFIED DATABASE OPERATIONS
# ============================================

async def query_database(query: str, params: Optional[list] = None) -> list:
    """
    Unified database query that tries PostgreSQL first, falls back to Supabase.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of results
    """
    # Try PostgreSQL first
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)
                return [dict(row) for row in result]
        except asyncpg.PostgresError as e:
            logger.warning("PostgreSQL query failed, falling back to Supabase: %s", e)
    
    # Fallback to Supabase
    client = get_supabase()
    if client:
        try:
            # Convert SQL query to Supabase query (simplified)
            # This is a basic implementation - in production, you'd need more sophisticated conversion
            table_name = extract_table_name(query)
            if table_name:
                # Simple SELECT query conversion
                if query.strip().upper().startswith("SELECT"):
                    response = client.table(table_name).select("*").execute()
                    return response.data
        except ValueError as e:
            logger.error("Supabase query also failed: %s", e)
    
    logger.error("No database connection available")
    return []


def extract_table_name(query: str) -> Optional[str]:
    """Extract table name from SQL query (simplified)."""
    query = query.strip().upper()
    
    if query.startswith("SELECT"):
        # Extract table name from SELECT ... FROM table ...
        parts = query.split("FROM")
        if len(parts) > 1:
            table_part = parts[1].strip().split()[0]
            return table_part.strip('"').strip("'")
    
    elif query.startswith("INSERT INTO"):
        # Extract table name from INSERT INTO table ...
        parts = query.split("INTO")
        if len(parts) > 1:
            table_part = parts[1].strip().split()[0]
            return table_part.strip('"').strip("'")
    
    elif query.startswith("UPDATE"):
        # Extract table name from UPDATE table ...
        parts = query.split("UPDATE")
        if len(parts) > 1:
            table_part = parts[1].strip().split()[0]
            return table_part.strip('"').strip("'")
    
    elif query.startswith("DELETE FROM"):
        # Extract table name from DELETE FROM table ...
        parts = query.split("FROM")
        if len(parts) > 1:
            table_part = parts[1].strip().split()[0]
            return table_part.strip('"').strip("'")
    
    return None


async def execute_query(query: str, params: Optional[list] = None) -> bool:
    """Execute a database query (INSERT, UPDATE, DELETE)."""
    pool = await get_db_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                if params:
                    await conn.execute(query, *params)
                else:
                    await conn.execute(query)
                return True
        except asyncpg.PostgresError as e:
            logger.warning("PostgreSQL execute failed: %s", e)
    
    # Note: Supabase doesn't support arbitrary SQL execution
    # You'd need to use their specific methods for each operation
    logger.error("Cannot execute query - no PostgreSQL connection available")
    return False


async def fetch_one(query: str, params: Optional[list] = None) -> Optional[Dict[str, Any]]:
    """Fetch a single row from the database."""
    results = await query_database(query, params)
    return results[0] if results else None


async def fetch_val(query: str, params: Optional[list] = None) -> Any:
    """Fetch a single value from the database."""
    result = await fetch_one(query, params)
    if result:
        # Return the first value in the row
        return list(result.values())[0] if result else None
    return None


# ============================================
# SPECIFIC QUERIES FOR OUR APPLICATION
# ============================================

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address."""
    query = "SELECT * FROM users WHERE email = $1"
    return await fetch_one(query, [email])


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    query = "SELECT * FROM users WHERE id = $1"
    return await fetch_one(query, [user_id])


async def get_organization_by_id(org_id: str) -> Optional[Dict[str, Any]]:
    """Get organization by ID."""
    query = "SELECT * FROM organizations WHERE id = $1"
    return await fetch_one(query, [org_id])


async def get_organization_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Get organization by slug."""
    query = "SELECT * FROM organizations WHERE slug = $1"
    return await fetch_one(query, [slug])


async def create_user(user_data: Dict[str, Any]) -> Optional[str]:
    """Create a new user and return the user ID."""
    query = """
        INSERT INTO users (email, password_hash, full_name, role, school_id, phone)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    
    params = [
        user_data["email"],
        user_data["password_hash"],
        user_data["full_name"],
        user_data["role"],
        user_data.get("school_id"),
        user_data.get("phone")
    ]
    
    return await fetch_val(query, params)


async def create_organization(org_data: Dict[str, Any]) -> Optional[str]:
    """Create a new organization and return the organization ID."""
    query = """
        INSERT INTO organizations (name, slug, email, phone, address, subscription_plan_id, trial_ends_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    """
    
    params = [
        org_data["name"],
        org_data["slug"],
        org_data["email"],
        org_data.get("phone"),
        org_data.get("address"),
        org_data.get("subscription_plan_id", "trial"),
        org_data.get("trial_ends_at")
    ]
    
    return await fetch_val(query, params)


# ============================================
# INITIALIZATION AND CLEANUP
# ============================================

async def initialize_database():
    """Initialize database connections."""
    logger.info("Initializing database connections...")
    
    # Try PostgreSQL
    if settings.database_available:
        try:
            await get_db_pool()
            if await test_db_connection():
                logger.info("✅ PostgreSQL connection established")
            else:
                logger.warning("⚠️  PostgreSQL connection test failed")
        except (asyncpg.PostgresError, ConnectionError) as e:
            logger.warning("⚠️  PostgreSQL initialization failed: %s", e)
    
    # Try Supabase
    if settings.supabase_available:
        if test_supabase_connection():
            logger.info("✅ Supabase connection established")
        else:
            logger.warning("⚠️  Supabase connection test failed")
    
    # Check if we have any database connection
    try:
        pool = await get_db_pool()
    except (asyncpg.PostgresError, ConnectionError):
        pool = None
    
    client = get_supabase()
    
    if not pool and not client:
        logger.error("❌ No database connection available")
        logger.error("   Please check your DATABASE_URL and SUPABASE configuration")
    elif pool and client:
        logger.info("✅ Both PostgreSQL and Supabase connections available")
    elif pool:
        logger.info("✅ PostgreSQL connection available (Supabase not configured)")
    elif client:
        logger.info("✅ Supabase connection available (PostgreSQL not configured)")


async def cleanup_database():
    """Clean up database connections."""
    logger.info("Cleaning up database connections...")
    await close_db_pool()
    logger.info("Database cleanup complete")


# ============================================
# HEALTH CHECK
# ============================================

async def check_database_health() -> Dict[str, Any]:
    """Check database health status."""
    health = {
        "postgresql": {
            "available": False,
            "error": None
        },
        "supabase": {
            "available": False,
            "error": None
        },
        "overall": False
    }
    
    # Check PostgreSQL
    try:
        pool = await get_db_pool()
        if pool and await test_db_connection():
            health["postgresql"]["available"] = True
        else:
            health["postgresql"]["error"] = "Connection failed or not configured"
    except (asyncpg.PostgresError, ConnectionError, ValueError) as e:
        health["postgresql"]["error"] = str(e)
    
    # Check Supabase
    try:
        client = get_supabase()
        if client and test_supabase_connection():
            health["supabase"]["available"] = True
        else:
            health["supabase"]["error"] = "Connection failed or not configured"
    except ValueError as e:
        health["supabase"]["error"] = str(e)
    
    # Overall health
    health["overall"] = health["postgresql"]["available"] or health["supabase"]["available"]
    
    return health